import os
import config
print(f'POSIP : {config.config.Config_machine_ip()} || POSPORT : {config.config.Config_Indoor_port()} || REQUEST FORMAT : {config.config.request_format()}')
os.system("python manage.py runserver")