import json

from database.db import get_connection


class AttemptManager:
    @staticmethod
    def _error_fields(result):
        error = result.get("error")
        if isinstance(error, dict):
            return error.get("error_name"), error.get("category")
        if error:
            return error.error_name, error.category
        return None, None

    @staticmethod
    def _output(result):
        return str(result.get("actual_output", result.get("output", "")) or "").strip()

    @staticmethod
    def _is_verified(result, expected_output):
        if expected_output is None:
            return False
        actual = AttemptManager._output(result)
        expected = str(expected_output).strip()
        return result.get("status") == "correct" and actual == expected

    def save_attempt(
        self,
        language,
        code,
        result,
        explanation,
        expected_output=None,
        source="code",
        question_key=None,
        stdin_input=None
    ):
        error_name, category = self._error_fields(result)
        concept = explanation.get("concept")
        actual_output = self._output(result)
        solved = self._is_verified(result, expected_output)

        with get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO attempts (
                    language, code, status, error_name, category, concept,
                    expected_output, actual_output, explanation, solved,
                    latest_code, latest_status, latest_retry_solved,
                    source, question_key, stdin_input, resolved_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?,
                        CASE WHEN ? = 1 THEN CURRENT_TIMESTAMP ELSE NULL END)
            """, (
                language, code, result.get("status"), error_name, category,
                concept, expected_output, actual_output, json.dumps(explanation),
                int(solved), code, result.get("status"), source, question_key,
                stdin_input, int(solved)
            ))
            return cursor.lastrowid

    def get_attempt(self, attempt_id):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM attempts WHERE id = ?", (attempt_id,)
            ).fetchone()
        return dict(row) if row else None

    def save_hint(self, attempt_id, level, hint):
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO hints (attempt_id, level, hint) VALUES (?, ?, ?)",
                (attempt_id, level, hint)
            )

    def get_hints(self, attempt_id):
        with get_connection() as conn:
            rows = conn.execute("""
                SELECT id, level, hint, created_at
                FROM hints WHERE attempt_id = ?
                ORDER BY id
            """, (attempt_id,)).fetchall()
        return [dict(row) for row in rows]

    def save_retry(self, attempt_id, code, result, expected_output=None):
        attempt = self.get_attempt(attempt_id)
        if not attempt:
            return None

        if expected_output is None:
            expected_output = attempt.get("expected_output")

        if expected_output is not None:
            expected_output = str(expected_output)

        status = result.get("status")
        actual_output = self._output(result)
        solved = self._is_verified(result, expected_output)
        error_name, _ = self._error_fields(result)

        with get_connection() as conn:
            conn.execute("""
                INSERT INTO retry_submissions (
                    attempt_id, code, status, error_name, actual_output,
                    expected_output, solved
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                attempt_id, code, status, error_name, actual_output,
                expected_output, int(solved)
            ))

            conn.execute("""
                UPDATE attempts
                SET retry_count = retry_count + 1,
                    latest_code = ?,
                    latest_status = ?,
                    latest_retry_solved = ?,
                    solved = MAX(solved, ?),
                    resolved_at = CASE
                        WHEN ? = 1 THEN CURRENT_TIMESTAMP
                        ELSE resolved_at
                    END
                WHERE id = ?
            """, (
                code, status, int(solved), int(solved), int(solved), attempt_id
            ))

        return {
            "attempt_id": attempt_id,
            "status": status,
            "error_name": error_name,
            "actual_output": actual_output,
            "expected_output": expected_output,
            "resolved": status == "correct" and (
                expected_output is None or solved
            ),
            "verified": solved,
            "solved": solved
        }

    def get_retry_history(self, attempt_id):
        with get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM retry_submissions
                WHERE attempt_id = ? ORDER BY id ASC
            """, (attempt_id,)).fetchall()
        return [dict(row) for row in rows]

    def list_attempts(self, limit=50, offset=0):
        with get_connection() as conn:
            rows = conn.execute("""
                SELECT id, language, code, status, error_name, category,
                       concept, expected_output, actual_output, solved,
                       retry_count, latest_code, latest_status,
                       latest_retry_solved, source, question_key, created_at
                FROM attempts
                ORDER BY id DESC LIMIT ? OFFSET ?
            """, (limit, offset)).fetchall()
        return [dict(row) for row in rows]
