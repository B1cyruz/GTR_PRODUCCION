import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor('#64748b'))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(36, 11 * inch - 28, "GTR LOGISTICS PLATFORM — MANUAL OFICIAL DE DESPLIEGUE A PRODUCCIÓN")
            self.drawRightString(8.5 * inch - 36, 11 * inch - 28, "DIGITALOCEAN & GITHUB")
            self.setStrokeColor(colors.HexColor('#cbd5e1'))
            self.setLineWidth(0.5)
            self.line(36, 11 * inch - 32, 8.5 * inch - 36, 11 * inch - 32)

        # Footer
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor('#64748b'))
        self.drawString(36, 25, "Confidencial • Sistema de Gestión de Rutas y Logística GTR")
        page_str = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(8.5 * inch - 36, 25, page_str)
        self.setStrokeColor(colors.HexColor('#cbd5e1'))
        self.setLineWidth(0.5)
        self.line(36, 35, 8.5 * inch - 36, 35)
        self.restoreState()


def build_deployment_pdf(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=42,
        bottomMargin=42
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        alignment=0
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#0284c7'),
        alignment=0
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=10,
        spaceAfter=4
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#0369a1'),
        spaceBefore=6,
        spaceAfter=3
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#334155')
    )

    body_bold = ParagraphStyle(
        'BodyBoldCustom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#0f172a')
    )

    code_style = ParagraphStyle(
        'CodeStyleCustom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.8,
        leading=10.5,
        textColor=colors.HexColor('#0f172a')
    )

    callout_style = ParagraphStyle(
        'CalloutStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor('#0369a1')
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor('#1e293b')
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor('#0f172a')
    )

    story = []

    # BANNER SUPERIOR
    story.append(Paragraph("GTR LOGISTICS PLATFORM", title_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph("GUÍA INTEGRAL DE PRODUCCIÓN: RESPALDO, GITHUB Y DESPLIEGUE EN DIGITALOCEAN", subtitle_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Versión:</b> 2.0 Producción &nbsp;|&nbsp; <b>Stack:</b> Django 5.2 + PostgreSQL 16 + Gunicorn + Nginx + Ubuntu 24.04 LTS", body_style))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#0284c7'), spaceBefore=2, spaceAfter=8))

    # RESUMEN EJECUTIVO / ARQUITECTURA
    story.append(Paragraph("1. ARQUITECTURA DEL DESPLIEGUE EN PRODUCCIÓN", h1_style))
    
    arch_flow_data = [
        [
            Paragraph("<b>1. Código Local & Backup</b><br/>• Exportar <b>GTR_PRODUCCION.zip</b><br/>• Limpieza de venv y cachés<br/>• Control de versiones Git", table_cell_style),
            Paragraph("<b>2. GitHub Repositorio Privado</b><br/>• Repositorio Seguro (Privado)<br/>• Rama <code>main</code> protegida<br/>• Deploy Key / Token SSH", table_cell_style),
            Paragraph("<b>3. DigitalOcean VPS Droplet</b><br/>• Ubuntu 24.04 LTS (1-2 GB RAM)<br/>• PostgreSQL 16 (DB: gtr_db)<br/>• Python 3.12 + Gunicorn WSGI<br/>• Nginx + SSL HTTPS Let's Encrypt", table_cell_style)
        ]
    ]
    arch_table = Table(arch_flow_data, colWidths=[2.5*inch, 2.5*inch, 2.5*inch])
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#f1f5f9')),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#e0f2fe')),
        ('BACKGROUND', (2, 0), (2, 0), colors.HexColor('#f0fdf4')),
        ('BOX', (0, 0), (0, 0), 1, colors.HexColor('#94a3b8')),
        ('BOX', (1, 0), (1, 0), 1, colors.HexColor('#0284c7')),
        ('BOX', (2, 0), (2, 0), 1, colors.HexColor('#16a34a')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(arch_table)
    story.append(Spacer(1, 8))

    # FASE 1
    story.append(Paragraph("2. FASE 1: GENERACIÓN DEL BACKUP Y PAQUETE LIMPIO (GTR_PRODUCCION.ZIP)", h1_style))
    story.append(Paragraph("Antes de subir el proyecto, se empaqueta una versión limpia excluyendo entornos virtuales locales (<code>venv</code>), claves temporales y cachés:", body_style))
    story.append(Spacer(1, 3))

    code_phase1 = (
        "# Ejecutar en PowerShell / Terminal local para generar el ZIP limpio:\n"
        "python -c \"import zipfile, os; z=zipfile.ZipFile('GTR_PRODUCCION.zip','w',zipfile.ZIP_DEFLATED); [z.write(os.path.join(r,f), os.path.relpath(os.path.join(r,f),'.')) for r,d,fs in os.walk('.') for f in fs if not any(x in r for x in ['venv','.git','__pycache__']) and f not in ['GTR_PRODUCCION.zip','.env']]; z.close(); print('Backup generado')\""
    )
    t_code1 = Table([[Paragraph(code_phase1, code_style)]], colWidths=[7.5*inch])
    t_code1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_code1)
    story.append(Spacer(1, 8))

    # FASE 2: GITHUB
    story.append(Paragraph("3. FASE 2: SUBIDA AL REPOSITORIO PRIVADO DE GITHUB", h1_style))
    story.append(Paragraph("Sube el código fuente a un repositorio privado para control de versiones y despliegue automatizado:", body_style))
    story.append(Spacer(1, 3))

    code_phase2 = (
        "1. Crear un nuevo repositorio en GitHub (Marcar como PRIVATE): 'gtr-logistics'\n"
        "2. En la terminal de tu máquina local (dentro de la carpeta del proyecto):\n"
        "   git init\n"
        "   git add .\n"
        "   git commit -m \"feat: Release GTR Producción v2.0 con soporte DigitalOcean\"\n"
        "   git branch -M main\n"
        "   git remote add origin https://github.com/TU_USUARIO_GITHUB/gtr-logistics.git\n"
        "   git push -u origin main"
    )
    t_code2 = Table([[Paragraph(code_phase2, code_style)]], colWidths=[7.5*inch])
    t_code2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_code2)
    story.append(Spacer(1, 8))

    # FASE 3: CREAR DROPLET
    story.append(Paragraph("4. FASE 3: CREACIÓN DEL DROPLET EN DIGITALOCEAN", h1_style))
    droplet_specs = [
        [Paragraph("Parámetro", table_header_style), Paragraph("Opción Recomendada", table_header_style), Paragraph("Justificación Técnica", table_header_style)],
        [Paragraph("Sistema Operativo", table_cell_bold), Paragraph("Ubuntu 24.04 LTS (x64)", table_cell_style), Paragraph("Compatibilidad nativa con Python 3.12 y PostgreSQL 16.", table_cell_style)],
        [Paragraph("Tipo de Plan", table_cell_bold), Paragraph("Basic / Regular (1 GB o 2 GB RAM)", table_cell_style), Paragraph("Excelente balance costo/rendimiento para Gunicorn + Nginx.", table_cell_style)],
        [Paragraph("Región", table_cell_bold), Paragraph("Miami (MIA1) o New York (NYC3)", table_cell_style), Paragraph("Menor latencia de red para usuarios en Colombia / Latinoamérica.", table_cell_style)],
        [Paragraph("Autenticación", table_cell_bold), Paragraph("SSH Keys (Recomendado)", table_cell_style), Paragraph("Máxima seguridad para acceso root y automatización.", table_cell_style)],
    ]
    t_droplet = Table(droplet_specs, colWidths=[1.5*inch, 2.3*inch, 3.7*inch])
    t_droplet.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t_droplet)
    story.append(Spacer(1, 8))

    # FASE 4: DESPLIEGUE EN VPS
    story.append(Paragraph("5. FASE 4: DESPLIEGUE AUTOMATIZADO O MANUAL EN EL VPS", h1_style))
    story.append(Paragraph("Conéctate por SSH a tu servidor y ejecuta el aprovisionamiento:", body_style))
    story.append(Spacer(1, 3))

    code_phase4 = (
        "# 1. Conexión SSH al Droplet\n"
        "ssh root@TU_IP_DIGITALOCEAN\n\n"
        "# 2. Clonar desde GitHub privado (usando Personal Access Token o Deploy Key):\n"
        "git clone https://TU_TOKEN@github.com/TU_USUARIO_GITHUB/gtr-logistics.git /var/www/gtr\n"
        "# (O si prefieres transferir GTR_PRODUCCION.zip desde local: scp GTR_PRODUCCION.zip root@TU_IP:/var/www/)\n\n"
        "# 3. Ejecutar Despliegue Automatizado con deploy.sh:\n"
        "cd /var/www/gtr\n"
        "chmod +x deploy.sh\n"
        "./deploy.sh"
    )
    t_code4 = Table([[Paragraph(code_phase4, code_style)]], colWidths=[7.5*inch])
    t_code4.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_code4)
    story.append(Spacer(1, 8))

    # PASO A PASO DETALLADO
    story.append(Paragraph("6. CONFIGURACIÓN MANUAL DETALLADA DE SERVICIOS (SYSTEMD & NGINX)", h1_style))
    
    code_manual = (
        "# A. Variables de Entorno en /var/www/gtr/.env\n"
        "SECRET_KEY=gtr-prod-secret-key-super-segura-2026-xyz\n"
        "DEBUG=False\n"
        "ALLOWED_HOSTS=TU_IP,tudominio.com,www.tudominio.com\n"
        "POSTGRES_DB=gtr_db\n"
        "POSTGRES_USER=gtr_user\n"
        "POSTGRES_PASSWORD=PasswordUltraSeguro2026!\n"
        "POSTGRES_HOST=localhost\n"
        "POSTGRES_PORT=5432\n\n"
        "# B. Servicio Systemd: /etc/systemd/system/gtr.service\n"
        "[Unit]\n"
        "Description=GTR Logistics Django Gunicorn Daemon\n"
        "After=network.target postgresql.service\n\n"
        "[Service]\n"
        "User=root\n"
        "WorkingDirectory=/var/www/gtr\n"
        "ExecStart=/var/www/gtr/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 gtr_project.wsgi:application\n"
        "Restart=always\n\n"
        "[Install]\n"
        "WantedBy=multi-user.target\n\n"
        "# C. Activar Servicio y Nginx\n"
        "systemctl daemon-reload && systemctl enable gtr.service && systemctl restart gtr.service\n"
        "cp /var/www/gtr/nginx.conf /etc/nginx/sites-available/gtr\n"
        "ln -sf /etc/nginx/sites-available/gtr /etc/nginx/sites-enabled/\n"
        "rm -f /etc/nginx/sites-enabled/default && nginx -t && systemctl restart nginx"
    )
    t_code_manual = Table([[Paragraph(code_manual, code_style)]], colWidths=[7.5*inch])
    t_code_manual.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0f172a')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#0284c7')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    # For dark background table cell style
    code_white_style = ParagraphStyle(
        'CodeWhite',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.2,
        leading=9.8,
        textColor=colors.HexColor('#38bdf8')
    )
    t_code_manual_content = Table([[Paragraph(code_manual.replace('\n', '<br/>'), code_white_style)]], colWidths=[7.5*inch])
    t_code_manual_content.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0f172a')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#0284c7')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_code_manual_content)
    story.append(Spacer(1, 8))

    # FASE 5: SSL Y CERTIFICADO
    story.append(Paragraph("7. CERTIFICADO SSL HTTPS GRATIS (LET'S ENCRYPT / CERTBOT)", h1_style))
    story.append(Paragraph("Para activar navegación cifrada segura (HTTPS) en tu dominio oficial:", body_style))
    story.append(Spacer(1, 3))

    code_ssl = (
        "# 1. Instalar Certbot con soporte Nginx:\n"
        "apt-get install -y certbot python3-certbot-nginx\n\n"
        "# 2. Obtener e instalar certificado automático (renovación automática incluida):\n"
        "certbot --nginx -d tudominio.com -d www.tudominio.com\n\n"
        "# 3. Verificar estado del certificado y simulación de renovación:\n"
        "certbot renew --dry-run"
    )
    t_ssl = Table([[Paragraph(code_ssl, code_style)]], colWidths=[7.5*inch])
    t_ssl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_ssl)
    story.append(Spacer(1, 8))

    # FASE 6: COMANDOS DE MONITOREO
    story.append(Paragraph("8. COMANDOS OPERATIVOS Y DE MANTENIMIENTO", h1_style))
    
    commands_data = [
        [Paragraph("Operación", table_header_style), Paragraph("Comando en Ubuntu", table_header_style), Paragraph("Descripción", table_header_style)],
        [Paragraph("Ver estado de la app", table_cell_bold), Paragraph("<code>systemctl status gtr.service</code>", table_cell_style), Paragraph("Comprueba que Gunicorn esté activo y respondiendo.", table_cell_style)],
        [Paragraph("Logs en tiempo real", table_cell_bold), Paragraph("<code>journalctl -u gtr.service -f</code>", table_cell_style), Paragraph("Muestra peticiones HTTP, errores y logs de Django.", table_cell_style)],
        [Paragraph("Reiniciar servidor", table_cell_bold), Paragraph("<code>systemctl restart gtr.service</code>", table_cell_style), Paragraph("Aplica cambios en el código Python de forma instantánea.", table_cell_style)],
        [Paragraph("Logs de Nginx", table_cell_bold), Paragraph("<code>tail -f /var/log/nginx/gtr_error.log</code>", table_cell_style), Paragraph("Monitorea posibles fallas de proxy o subida de imágenes.", table_cell_style)],
        [Paragraph("Backup Base de Datos", table_cell_bold), Paragraph("<code>pg_dump -U gtr_user gtr_db > backup.sql</code>", table_cell_style), Paragraph("Genera un volcado SQL completo de la base de datos.", table_cell_style)],
        [Paragraph("Ejecutar Migraciones", table_cell_bold), Paragraph("<code>/var/www/gtr/venv/bin/python manage.py migrate</code>", table_cell_style), Paragraph("Actualiza la estructura de tablas de la base de datos.", table_cell_style)],
    ]
    t_cmd = Table(commands_data, colWidths=[1.5*inch, 2.8*inch, 3.2*inch])
    t_cmd.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t_cmd)

    doc.build(story, canvasmaker=NumberedCanvas)


if __name__ == '__main__':
    root_pdf1 = 'MANUAL_DESPLIEGUE_PRODUCCION_GTR.pdf'
    root_pdf2 = 'GUIA_DESPLIEGUE_DIGITALOCEAN_GTR.pdf'
    
    media_dir = 'media'
    os.makedirs(media_dir, exist_ok=True)
    media_pdf1 = os.path.join(media_dir, 'MANUAL_DESPLIEGUE_PRODUCCION_GTR.pdf')
    media_pdf2 = os.path.join(media_dir, 'GUIA_DESPLIEGUE_DIGITALOCEAN_GTR.pdf')
    
    build_deployment_pdf(root_pdf1)
    build_deployment_pdf(root_pdf2)
    build_deployment_pdf(media_pdf1)
    build_deployment_pdf(media_pdf2)
    
    print(f"PDFs generados correctamente:\n- {root_pdf1}\n- {root_pdf2}\n- {media_pdf1}\n- {media_pdf2}")
