from flask import Flask, request, render_template, redirect, url_for, send_file, flash
import datetime, os, json, io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = 'troque-esta-chave-para-producao'

ARQUIVO_BASE = "receitas.txt"
MEDICO_CONFIG = "medico.json"

def carregar_medico():
    if os.path.exists(MEDICO_CONFIG):
        with open(MEDICO_CONFIG, "r", encoding="utf-8") as f:
            return json.load(f)
   
    return { "nome_medico": "", "crm_medico": "", "clinica": "" }

def salvar_medico(cfg):
    with open(MEDICO_CONFIG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def buscar_receita(sintomas):
    sintomas = sintomas.strip().lower()
    if not os.path.exists(ARQUIVO_BASE):
        return None
    with open(ARQUIVO_BASE, "r", encoding="utf-8") as f:
        linhas = [l.rstrip('\n') for l in f.readlines()]
    for i in range(0, len(linhas), 2):
        sintoma_linha = linhas[i].strip().lower()
        if sintoma_linha == sintomas:
            
            if i+1 < len(linhas):
                return linhas[i+1].strip()
    return None

def salvar_receita(sintomas, receita):
    with open(ARQUIVO_BASE, "a", encoding="utf-8") as f:
        f.write(sintomas.strip().lower() + "\n")
        f.write(receita.strip() + "\n")

def gerar_pdf_receita(paciente, receita, nome_medico, crm_medico, clinica):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    data_atual = datetime.datetime.now().strftime("%d/%m/%Y")

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(300, 800, "RECEITUÁRIO MÉDICO")

    c.setFont("Helvetica", 12)
    c.drawString(50, 770, f"Médico: {nome_medico}")
    c.drawString(50, 750, f"CRM: {crm_medico}")
    c.drawString(50, 730, f"Clínica: {clinica}")
    c.drawString(50, 710, f"Data: {data_atual}")

    c.line(50, 700, 550, 700)

    c.drawString(50, 680, f"Paciente: {paciente}")
    c.drawString(50, 660, "Prescrição:")

    text_obj = c.beginText(50, 640)
    text_obj.setFont("Helvetica", 12)
    for linha in str(receita).split("\n"):
        text_obj.textLine(linha)
    c.drawText(text_obj)

    c.line(50, 100, 250, 100)
    c.drawString(50, 85, "Assinatura do Médico")

    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer

@app.route("/", methods=["GET", "POST"])
def index():
    medico = carregar_medico()
    if request.method == "POST":
        paciente = request.form.get("paciente","").strip()
        sintomas = request.form.get("sintomas","").strip()
        if not paciente or not sintomas:
            flash("Preencha paciente e sintomas.", "warning")
            return redirect(url_for('index'))

        receita = buscar_receita(sintomas)
        if receita:
            
            pdf_buf = gerar_pdf_receita(paciente, receita, medico.get("nome_medico",""), medico.get("crm_medico",""), medico.get("clinica",""))
            return send_file(pdf_buf, as_attachment=True, download_name="receituario.pdf", mimetype="application/pdf")
        else:
            
            return render_template("add_receita.html", paciente=paciente, sintomas=sintomas, medico=medico)
    return render_template("index.html", medico=medico)

@app.route("/salvar_receita", methods=["POST"])
def rota_salvar_receita():
    paciente = request.form.get("paciente","").strip()
    sintomas = request.form.get("sintomas","").strip()
    nova_receita = request.form.get("nova_receita","").strip()
    if not sintomas or not nova_receita:
        flash("Sintomas e receita são obrigatórios.", "warning")
        return redirect(url_for('index'))
    salvar_receita(sintomas, nova_receita)
    flash("Receita salva com sucesso.", "success")
    return redirect(url_for('index'))

@app.route("/config", methods=["GET", "POST"])
def config_medico():
    medico = carregar_medico()
    if request.method == "POST":
        nome_medico = request.form.get("nome_medico","").strip()
        crm_medico = request.form.get("crm_medico","").strip()
        clinica = request.form.get("clinica","").strip()
        cfg = {"nome_medico": nome_medico, "crm_medico": crm_medico, "clinica": clinica}
        salvar_medico(cfg)
        flash("Configurações do médico salvas.", "success")
        return redirect(url_for('index'))
    return render_template("config_medico.html", medico=medico)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

