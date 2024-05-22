import logging
import os
import azure.functions as func

app = func.FunctionApp()

@app.schedule(schedule="0 * * * * *", arg_name="myTimer", run_on_startup=True,
              use_monitor=False) 
def timer_trigger(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')

#    env_var_value = func.current_function().get_function_env("FUNCTIONS_WORKER_RUNTIME")
#    logging.info("my environment value=",env_var_value)
    my_variable = os.getenv("FUNCTIONS_WORKER_RUNTIME")
    logging.info(f"My environment variable value: {my_variable}")

    logging.info('Python timer trigger function executed.')