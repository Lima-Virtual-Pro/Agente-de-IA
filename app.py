import os, httpx, sympy, re
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

KEY = os.getenv("GEMINI_KEY", "")
URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

app = FastAPI()

class P(BaseModel):
    pergunta: str

HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agente</title>
<style>
*{box-sizing:border-box;margin:0}
body{font-family:system-ui;background:#0f172a;color:#e2e8f0;display:flex;flex-direction:column;height:100dvh}
header{padding:1rem;background:#1e293b;text-align:center;font-weight:600}
#chat{flex:1;overflow-y:auto;padding:1rem;display:flex;flex-direction:column;gap:.75rem}
.msg{max-width:85%;padding:.75rem 1rem;border-radius:1rem;line-height:1.4;white-space:pre-wrap}
.user{align-self:flex-end;background:#2563eb}
.bot{align-self:flex-start;background:#334155}
form{display:flex;gap:.5rem;padding:.75rem;background:#1e293b}
input{flex:1;padding:.75rem;border-radius:.75rem;border:none;background:#0f172a;color:#e2e8f0;font-size:16px}
button{padding:.75rem 1rem;border-radius:.75rem;border:none;background:#2563eb;color:#fff;font-weight:600}
button:disabled{opacity:.5}
</style>
</head>
<body>
<header>🤖 Agente</header>
<div id="chat"></div>
<form id="form">
<input id="pergunta" placeholder="Pergunte algo..." autocomplete="off" required>
<button id="enviar" type="submit">Enviar</button>
</form>
<script>
const chat=document.getElementById("chat");
const form=document.getElementById("form");
const input=document.getElementById("pergunta");
const btn=document.getElementById("enviar");
function add(tipo,txt){const d=document.createElement("div");d.className="msg "+tipo;d.textContent=txt;chat.appendChild(d);chat.scrollTop=chat.scrollHeight;}
form.addEventListener("submit",async(e)=>{
  e.preventDefault();const q=input.value.trim();if(!q)return;
  add("user",q);input.value="";btn.disabled=true;add("bot","...");
  const ph=chat.lastChild;
  try{
    const r=await fetch("/perguntar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({pergunta:q})});
    const d=await r.json();ph.textContent=d.resposta;
  }catch(err){ph.textContent="Erro de conexão.";}finally{btn.disabled=false;input.focus();}
});
</script>
</body>
</html>
"""

async def gemini(prompt: str, system: str) -> str:
    body = {"contents": [{"parts": [{"text": prompt}]}], "systemInstruction": {"parts": [{"text": system}]}}
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(f"{URL}?key={KEY}", json=body)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

@app.get("/", response_class=HTMLResponse)
def raiz():
    return HTML

@app.post("/perguntar")
async def perguntar(b: P):
    q = b.pergunta
    try:
        num = re.search(r"[\d\s\+\-\*/\(\)\.]+", q)
        if num and any(op in num.group(0) for op in "+-*/"):
            try: return {"resposta": f"{sympy.sympify(num.group(0).strip())}"}
            except: pass
        system = "Você é um assistente útil. Responda em português, curto e direto."
        resposta = await gemini(q, system)
        return {"resposta": resposta}
    except Exception as e:
        return {"resposta": f"Erro: {e}"}
