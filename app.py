import streamlit as st
import mlflow
from mlflow.tracking import MlflowClient
from functools import partial
import os
from shutil import copyfile


def run_workflow(workflow_order):
    for workflow in workflow_order:
        res = os.system(f"python3 {os.path.join('src', workflow)}")
        if res!=0:
            st.error(f"An error occured while running {workflow}")

    if res==0:
        st.success("Workflow ran successfully \N{party popper}")

def run_tests():
    res = os.system('pytest -v .')
    if res != 0:
        st.error("Tests failed")
    if res==0:
        st.success("Tests ran successfully \N{party popper}")

def deploy_model(runs, model_name, client):
    tags = dict(runs[0])['data'].tags['mlflow.log-model.history']
    best_run_id = eval(tags)[0]['run_id']
    save_model_path = "models"

    for mv in client.search_model_versions(f"name='{model_name}'"): 
        mv = dict(mv)
        version = mv['version']
        run_id = mv['run_id']

        if run_id==best_run_id:
            client.transition_model_version_stage(
                name=model_name,
                version=version,
                stage='Production',
                archive_existing_versions=True
            )
            
            best_model_uri = client.get_model_version_download_uri(model_name, version)
            os.makedirs(save_model_path, exist_ok=True)
            for artifact in os.listdir(best_model_uri):
                artifact_path = os.path.join(best_model_uri, artifact)
                copyfile(artifact_path, os.path.join(save_model_path, artifact))
            
            st.success(
                f"Successfully transitioned {model_name} v{version} to production \N{party popper}"
                )

client = MlflowClient("http://127.0.0.1:5000", "http://127.0.0.1:5000")

src_files = os.listdir('src')

st.title("Run workflow")
workflow_order = st.multiselect(
     'Select the order of your workflow',
     src_files)

if workflow_order:
    st.button(
        'Run workflow', 
        on_click=partial(run_workflow, workflow_order=workflow_order)
        )

if os.path.exists('tests'):
    st.title("Unit tests")
    st.button(
        'Run tests',
        on_click=run_tests
    )

st.title("Deployment")
mlflow_experiments = (exp.name for exp in client.list_experiments())

exp_name = st.selectbox(
    'Select the experiment which contains the model to be deployed',
     mlflow_experiments)

exp_id = dict(client.get_experiment_by_name(exp_name))['experiment_id']
runs = client.search_runs([exp_id])

try:
    metric_list = dict(runs[0])['data'].metrics.keys()
except IndexError:
    metric_list = []

reg_models = [reg_model.name for reg_model in client.list_registered_models()]

if metric_list:
    metric = st.selectbox(
            "Select metrics to compare models",
            metric_list
        )
    runs = client.search_runs([exp_id], order_by=[f'metrics.{metric} DESC'])
    
    if reg_models:
        model_name = st.selectbox(
                "Select model name",
                reg_models
            )
        st.button(
            "Productionize best model",
            on_click=partial(
                deploy_model, runs=runs, 
                model_name=model_name, client=client,
                )
        )
