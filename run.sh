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

echo "Starting servers..."
airflow api-server & 
sleep 5

echo "Starting Airflow Scheduler..."
airflow scheduler & 
sleep 5

echo "Starting FastAPI Server..."
uvicorn app.main:app --reload  

wait