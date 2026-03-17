cleanup(){     
    echo ""
    echo "Stopping all project servers..."
    pkill -P $$
    exit 0
}

trap cleanup SIGINT

if [ -f "IMS_venv/bin/activate" ]; then
    source "IMS_venv/bin/activate"
else
    echo "No virtual environment found"
    exit 1
fi 

mkdir -p logs

export TZ="Asia/Kolkata"
export AIRFLOW_HOME="$(pwd)/airflow"

export AIRFLOW__CORE__DEFAULT_TIMEZONE="Asia/Kolkata"
export AIRFLOW__LOGGING__COLORED_CONSOLE_LOG="False"
export AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION="False"
export FASTAPI_HOST="${FASTAPI_HOST:-127.0.0.1}"
export FASTAPI_PORT="${FASTAPI_PORT:-8000}"

echo "Starting servers..."
airflow api-server 2>&1 | python3 log_filter.py > logs/airflow_api-server.log & 
sleep 5

echo "Starting Airflow DAG Processor..."
airflow dag-processor 2>&1 | python3 log_filter.py > logs/airflow_dag-processor.log &
sleep 5

echo "Starting Airflow Scheduler..."
airflow scheduler 2>&1 | python3 log_filter.py > logs/airflow_scheduler.log & 
sleep 5

echo "Starting FastAPI Server..."
uvicorn app.main:app --reload --host "$FASTAPI_HOST" --port "$FASTAPI_PORT" > logs/fastapi.log 2>&1 &

wait
