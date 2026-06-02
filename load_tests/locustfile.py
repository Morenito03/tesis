from locust import HttpUser, task, between, events
import time
import json

# Ajusta la ruta host cuando lances Locust: --host=http://127.0.0.1:8000

class MedistrustUser(HttpUser):
    wait_time = between(1, 2)  # tiempo entre tareas por usuario (ajustable)

    def on_start(self):
        # Si necesitas autenticación, hazlo aquí
        pass

    @task
    def ask_and_poll(self):
        """
        Flujo de prueba:
         1) POST /ask/ -> devuelve task_id
         2) Poll GET /result/{task_id} hasta finished|error o timeout
        Este flujo simula un usuario que hace una consulta y espera la respuesta.
        """
        question_examples = [
            "Total de consultas médicas en CMF 3 en enero 2024",
            "¿Cuántas consultas de diabetes se registraron en Enero 2024?",
            "Resumen de 'Consulta Médica 0-19' para CMF 5 en Marzo 2024",
            "Total general (CONSOLIDADO) enero 2024 GBT"
        ]
        payload = {"question": question_examples[int(time.time()*1000) % len(question_examples)]}

        start = time.time()
        with self.client.post("/ask/", json=payload, catch_response=True, name="/ask/") as resp:
            if resp.status_code != 200:
                resp.failure(f"/ask/ status {resp.status_code}")
                return
            try:
                data = resp.json()
                task_id = data.get("task_id") or data.get("taskId") or data.get("task")
            except Exception as e:
                resp.failure(f"invalid json from /ask/: {e}")
                return

            if not task_id:
                resp.failure("no task_id returned")
                return

        # Polling: timeout total 60s (ajústalo si tus consultas reales tardan más)
        timeout_seconds = 60
        interval = 1.0
        elapsed = 0.0
        final_answer = None
        while elapsed < timeout_seconds:
            r = self.client.get(f"/result/{task_id}", name="/result/{task_id}")
            if r.status_code != 200:
                # registra fallo del polling y sal
                break
            try:
                j = r.json()
            except Exception:
                break

            status = j.get("status")
            if status == "finished":
                final_answer = j.get("answer", "")
                break
            if status == "error":
                break

            time.sleep(interval)
            elapsed += interval

        total_time = time.time() - start
        # opcional: puedes anexar info a logs si lo deseas
        # events.request_success.fire(...)  # Locust registra automáticamente requests

        # Si no hubo respuesta, marca fallo (locust muestra fallo / successes)
        if final_answer is None:
            # Generar un request failed artificial para que se vea en los resultados
            events.request_failure.fire(
                request_type="ask_flow",
                name="ask_and_poll",
                response_time=int(total_time*1000),
                exception=Exception("No finished answer within timeout")
            )
        else:
            events.request_success.fire(
                request_type="ask_flow",
                name="ask_and_poll",
                response_time=int(total_time*1000),
                response_length=len(final_answer)
            )
