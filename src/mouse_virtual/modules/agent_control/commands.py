from dataclasses import dataclass
from urllib.parse import urlparse
ALLOWED_ACTIONS={"browser.open","browser.find_element","browser.fill","browser.click","browser.read_page","browser.search","desktop.find_control","desktop.fill","desktop.invoke","desktop.read_control","desktop.wait_text"}
@dataclass(frozen=True)
class Command:
    action:str
    url:str=""
    query:str=""
    role:str=""
    name:str=""
    text:str=""
    auto_id:str=""
    control_type:str="Edit"
    def validate(self):
        if self.action not in ALLOWED_ACTIONS:raise ValueError("Unsupported action")
        if self.url:
            parsed=urlparse(self.url)
            if parsed.scheme not in ("http","https") or not parsed.netloc:raise ValueError("Invalid browser URL")
        if any(len(s)>5000 for s in (self.url,self.query,self.role,self.name,self.text,self.auto_id,self.control_type)):
            raise ValueError("Command argument too long")
