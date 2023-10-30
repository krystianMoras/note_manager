import yaml
import subprocess
from pathlib import Path
import tempfile
import shutil
from pydantic import BaseModel
import json

class Event(BaseModel):
    title: str
    day: int
    month: int
    year: int
    time_start: str
    time_end: str
    location: str
    details: str

# read config.yaml
config = yaml.load(open("llama_config.yaml", "r"), Loader=yaml.FullLoader)


class LlamaClient:

    def __init__(self, config_path: Path):
        self.config = yaml.load(open(config_path, "r"), Loader=yaml.FullLoader)
        self.llama_cpp_executable = self.config["llama_cpp_executable"]
        self.llama_model = self.config["llama_model"]


    def prompt(self, prompt, grammar, prompt_cache_path = None):
        
        # open temporary folder

        with tempfile.TemporaryDirectory() as temp_dir:

            # save grammar to temporary file
            grammar_path = Path(temp_dir) / "grammar.gbnf"
            with open(grammar_path, "w") as f:
                f.write(grammar)

            # save prompt to temporary file
            prompt_path = Path(temp_dir) / "prompt.txt"
            with open(prompt_path, "w") as f:
                f.write(prompt)

            # copy prompt cache to temporary file
            prompt_cache_temp_path = Path(temp_dir) / "prompt_cache.bin"
            if prompt_cache_path is not None:
                shutil.copy(prompt_cache_path, prompt_cache_temp_path)


            # run subprocess
            

            command = [self.llama_cpp_executable,
                        "-m", self.llama_model,
                        "--temp" , "0",
                            "--grammar-file", grammar_path,
                            "--file", prompt_path,
                            "--prompt-cache", prompt_cache_temp_path]
            
            output = subprocess.run(command, capture_output=True)
            output = output.stdout.decode("utf-8")
            output = output[len(prompt)+9:]
            print(output)


            # parse output into Event object
            #validate json
            try:
                valid_json = json.loads(output)
                event = Event(**valid_json)
            except Exception as e:
                print(e)
                return None
            
            return event



if __name__ == "__main__":

    llama = LlamaClient("llama_config.yaml")

    grammar = r'''
root ::= Event
Event ::= "{" "\"title\":" string "," "\"day\":" day   "," "\"month\":" month   "," "\"year\":" year   "," "\"time_start\":" time   "," "\"time_end\":" time   "," "\"location\":"  string  "," "\"details\":" string  "," "\"when\":" string  "}"
string ::= "\""   [0-9a-zA-Z]+   "\""
number ::= [0-9]+   "."?   [0-9]*
day ::= ([0-9][0-9]) | "\"\""
month ::= ([0-9][0-9]) | "\"\""
year ::= ([0-9][0-9][0-9][0-9]) | "\"\""
time ::= ("\"" [0-9][0-9] ":" [0-9][0-9] "\"") | "\"\""

'''

    init_prompt = "Your task is to fill in a JSON template to extract the following information from the text:\n - title, descriptive but concise\n - day\n - month\n - year\n - additional details that were in the text\n - when, time description with natural language\n Use only information provided explicitly in the text, else leave it as an empty string\n"
    prompt = "Text:\nCoffee break at 10" + "\n JSON:\n"
    prompt = init_prompt + prompt
    print(llama.prompt(prompt, grammar))

