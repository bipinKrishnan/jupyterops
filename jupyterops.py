import io
import nbformat as nbf
import os
from typer import run
from shutil import copyfile

class JupyterOps:

  def extract_code(self, ipynb_name):
    ipynb_path = os.path.join(os.getcwd(), ipynb_name)
    save_file_path = 'extras'

    if os.path.exists(save_file_path):
      os.remove(save_file_path)

    with io.open(ipynb_path, 'r', encoding='utf-8') as f:
      self.nodes = nbf.read(f, as_version=4)

    for cell in self.nodes['cells']:
      cell_type = cell['cell_type']
      content = cell['source']

      if (cell_type=='code') and ("extract_code" in content):
        continue

      if (cell_type=='markdown') and (content.count('#')==1):
        save_file_path = content.replace('#', '').lstrip()
        if os.path.exists(save_file_path):
          os.remove(save_file_path)
        os.makedirs(os.path.dirname(save_file_path), exist_ok=True)

      if cell_type=='code':
        if save_file_path=='extras':
          continue
        curr_file_path = save_file_path
        with open(curr_file_path, 'a') as w:
          if os.path.getsize(curr_file_path)>0:
            w.write('\n\n')
          w.write(content)

  def create_app(self, main_dir):
    reqd_dirs = ['src']

    for name in reqd_dirs:
      complete_path = os.path.join(main_dir, name)
      app_file_name = 'app.py'
      app_dir = os.path.join(main_dir, app_file_name)

      if os.path.exists(complete_path):

        if os.path.isdir(complete_path):
          copyfile('app.py', app_dir)
          os.system(f"cd {main_dir} && streamlit run {app_file_name}")
        else:
          raise FileNotFoundError(f"'{name}' is not a directory")
          
      else:
        raise FileNotFoundError(f"Directory '{name}' does not exist in '{main_dir}'")

def main(ipynb_name, project_name):
  jo = JupyterOps()
  jo.extract_code(ipynb_name)
  jo.create_app(project_name)

  
if __name__=="__main__":
  run(main)
