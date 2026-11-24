from database.db import get_connection


class LearningAnalyzer:
    def get_progress(self):
        with get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
            solved = conn.execute("SELECT COUNT(*) FROM attempts WHERE solved = 1").fetchone()[0]
            practice_total = conn.execute(
                "SELECT COUNT(*) FROM attempts WHERE source IN ('practice', 'identify')"
            ).fetchone()[0]
            practice_solved = conn.execute(
                "SELECT COUNT(*) FROM attempts WHERE source IN ('practice', 'identify') AND solved = 1"
            ).fetchone()[0]
            retry_total = conn.execute(
                "SELECT COUNT(*) FROM retry_submissions"
            ).fetchone()[0]
            retry_solved = conn.execute(
                "SELECT COUNT(*) FROM retry_submissions WHERE solved = 1"
            ).fetchone()[0]
            concepts = conn.execute("""
                SELECT concept, COUNT(*) AS attempts,
                       SUM(CASE WHEN solved = 1 THEN 1 ELSE 0 END) AS solved
                FROM attempts
                WHERE concept IS NOT NULL
                GROUP BY concept
                ORDER BY attempts DESC
            """).fetchall()
            errors = conn.execute("""
                SELECT error_name, COUNT(*) AS count
                FROM attempts
                WHERE error_name IS NOT NULL
                GROUP BY error_name
                ORDER BY count DESC
            """).fetchall()
            categories = conn.execute("""
                SELECT category, COUNT(*) AS count FROM attempts
                WHERE category IS NOT NULL GROUP BY category ORDER BY count DESC
            """).fetchall()
            languages = conn.execute("""
                SELECT language, COUNT(*) AS attempts,
                       SUM(CASE WHEN solved = 1 THEN 1 ELSE 0 END) AS solved
                FROM attempts GROUP BY language ORDER BY attempts DESC
            """).fetchall()
            activity = conn.execute("""
                SELECT date(created_at) AS day, COUNT(*) AS attempts,
                       SUM(CASE WHEN solved = 1 THEN 1 ELSE 0 END) AS solved
                FROM attempts WHERE created_at >= date('now', '-13 days')
                GROUP BY day ORDER BY day
            """).fetchall()
            retried = conn.execute("""
                SELECT id, language, error_name, concept, retry_count, solved, created_at
                FROM attempts WHERE retry_count > 0 ORDER BY id DESC LIMIT 10
            """).fetchall()
            statuses = conn.execute("""
                SELECT status, COUNT(*) AS count
                FROM attempts
                GROUP BY status
            """).fetchall()

        accuracy = round((practice_solved / practice_total) * 100, 1) if practice_total else 0.0
        retry_rate = round((retry_solved / retry_total) * 100, 1) if retry_total else 0.0

        return {
            "total_attempts": total,
            "solved_attempts": solved,
            "unsolved_attempts": total - solved,
            "practice": {
                "total_submissions": practice_total,
                "solved_submissions": practice_solved,
                "incorrect_submissions": practice_total - practice_solved,
                "accuracy_percentage": accuracy
            },
            "retries": {
                "total_retries": retry_total,
                "verified_solved_retries": retry_solved,
                "success_percentage": retry_rate
            },
            "overall_accuracy_percentage": round(solved / total * 100, 1) if total else 0.0,
            "category_frequency": [dict(row) for row in categories],
            "language_frequency": [dict(row) for row in languages],
            "activity": [dict(row) for row in activity],
            "retry_history": [dict(row) for row in retried],
            "status_frequency": [dict(row) for row in statuses],
            "concept_frequency": [dict(row) for row in concepts],
            "error_frequency": [dict(row) for row in errors]
        }
