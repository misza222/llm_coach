
from jinja2 import Environment, FileSystemLoader
from config import Config

class SystemPrompter:
    def __init__(self):
        self.env = Environment(loader=FileSystemLoader([
            str(Config.TEMPLATES_DIR),           
            str(Config.MEMORY_DIR / "templates") 
        ]))
        
    def build_system_prompt(self, core, profile, session, history):
        template = self.env.get_template("main.j2")
        
        return template.render(
            core=core,
            profile=profile,
            session=session,
            history=history
        )   
