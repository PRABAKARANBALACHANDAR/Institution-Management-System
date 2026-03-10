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

export AIRFLOW__CORE__DEFAULT_TIMEZONE="Asia/Kolkata"
export AIRFLOW__LOGGING__COLORED_CONSOLE_LOG="False"

echo "Starting servers..."
airflow api-server 2>&1 | python3 log_filter.py > logs/airflow_api-server.log & 
sleep 5

echo "Starting Airflow Scheduler..."
airflow scheduler 2>&1 | python3 log_filter.py > logs/airflow_scheduler.log & 
sleep 5

echo "Starting FastAPI Server..."
uvicorn app.main:app --reload > logs/fastapi.log 2>&1 &

wait