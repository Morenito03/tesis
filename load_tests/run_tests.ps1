# run_tests.ps1
# Ejecuta Locust en modo headless para varias cargas y guarda CSVs
# Requisitos: tener locust en el venv activo (pip install locust)

$host = "http://127.0.0.1:8000"
$locustfile = "locustfile.py"
$duracion = "00:01:00"   # 1 minuto por prueba; ajusta si necesitas más tiempo
$users_list = @(5,10,15,20,30)

foreach ($u in $users_list) {
    $csvprefix = "locust_${u}u"
    Write-Host "== Ejecutando prueba con $u usuarios por 60s -> $csvprefix ============"
    & locust -f $locustfile --headless -u $u -r $u --run-time $duracion --host $host --csv $csvprefix
    Start-Sleep -Seconds 5
}
Write-Host "Todas las pruebas completadas."