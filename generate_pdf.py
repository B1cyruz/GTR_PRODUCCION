import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def create_pdf(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
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
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )

    body_bold = ParagraphStyle(
        'BodyBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#0f172a')
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#1e293b')
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#0f172a')
    )

    story = []

    # Header section
    story.append(Paragraph("GTR LOGISTICS - GESTIÓN Y RUTAS", title_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph("DOCUMENTO TÉCNICO OFICIAL: STACK TECNOLÓGICO Y ARQUITECTURA", subtitle_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Fecha de emisión:</b> 31 de Agosto de 2026 &nbsp;|&nbsp; <b>Infraestructura:</b> Ubuntu 24.04 LTS &nbsp;|&nbsp; <b>Servidor:</b> DigitalOcean Droplet VPS", body_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284c7'), spaceBefore=2, spaceAfter=10))

    # Section 1: Stack Tecnológico
    story.append(Paragraph("1. STACK TECNOLÓGICO OFICIAL DE PRODUCCIÓN", h1_style))
    story.append(Spacer(1, 4))

    stack_data = [
        [Paragraph("Capa", table_header_style), Paragraph("Tecnología", table_header_style), Paragraph("Versión / Detalle", table_header_style), Paragraph("Propósito Operativo", table_header_style)],
        [Paragraph("Backend", table_cell_bold), Paragraph("Python", table_cell_style), Paragraph("3.12", table_cell_style), Paragraph("Lógica de negocio, servicios geoespaciales y algoritmos.", table_cell_style)],
        [Paragraph("Framework Web", table_cell_bold), Paragraph("Django", table_cell_style), Paragraph("5.2.17 (>=5.0, <5.3)", table_cell_style), Paragraph("Arquitectura MVC, routing centralizado, seguridad y Auth.", table_cell_style)],
        [Paragraph("Base de Datos", table_cell_bold), Paragraph("PostgreSQL", table_cell_style), Paragraph("16", table_cell_style), Paragraph("Motor relacional transaccional e índices de búsqueda.", table_cell_style)],
        [Paragraph("ORM", table_cell_bold), Paragraph("Django ORM", table_cell_style), Paragraph("Nativo de Django", table_cell_style), Paragraph("Modelado declarativo y migraciones versionadas.", table_cell_style)],
        [Paragraph("Conector DB", table_cell_bold), Paragraph("psycopg2-binary", table_cell_style), Paragraph("2.9.12 (>=2.9.9)", table_cell_style), Paragraph("Driver de alto rendimiento para PostgreSQL 16.", table_cell_style)],
        [Paragraph("Servidor App", table_cell_bold), Paragraph("Gunicorn", table_cell_style), Paragraph("26.2.0 (>=21.2.0)", table_cell_style), Paragraph("Servidor de aplicaciones WSGI para producción.", table_cell_style)],
        [Paragraph("Servidor Proxy", table_cell_bold), Paragraph("Nginx", table_cell_style), Paragraph("Ubuntu 24.04", table_cell_style), Paragraph("Proxy reverso, SSL, compresión GZIP y buffer 50MB.", table_cell_style)],
        [Paragraph("Estáticos", table_cell_bold), Paragraph("WhiteNoise", table_cell_style), Paragraph("6.12.0 (>=6.6.0)", table_cell_style), Paragraph("Servidor integrado de assets con cache hashing.", table_cell_style)],
        [Paragraph("Imágenes", table_cell_bold), Paragraph("Pillow", table_cell_style), Paragraph("12.3.0 (>=10.2.0)", table_cell_style), Paragraph("Procesamiento de fotos de fachadas y comprobantes.", table_cell_style)],
        [Paragraph("Seguridad", table_cell_bold), Paragraph("Django Auth + BCrypt", table_cell_style), Paragraph("bcrypt 5.0.0", table_cell_style), Paragraph("RBAC (ROOT, COORDINADOR, REPARTIDOR) y PBKDF2.", table_cell_style)],
        [Paragraph("Configuración", table_cell_bold), Paragraph("python-dotenv", table_cell_style), Paragraph("1.2.3 (>=1.0.1)", table_cell_style), Paragraph("Variables de entorno (.env) y secretos aislados.", table_cell_style)],
        [Paragraph("APIs Externas", table_cell_bold), Paragraph("requests", table_cell_style), Paragraph("2.34.2 (>=2.31.0)", table_cell_style), Paragraph("Integración con servicios de geocodificación satelital.", table_cell_style)],
        [Paragraph("Frontend", table_cell_bold), Paragraph("HTML5 + CSS3 + JS", table_cell_style), Paragraph("Django Templates", table_cell_style), Paragraph("TailwindCSS (CDN), Leaflet.js y Material Symbols.", table_cell_style)],
        [Paragraph("SO Servidor", table_cell_bold), Paragraph("Ubuntu Server", table_cell_style), Paragraph("24.04 LTS", table_cell_style), Paragraph("Sistema operativo base para el droplet VPS.", table_cell_style)],
        [Paragraph("Cloud VPS", table_cell_bold), Paragraph("DigitalOcean", table_cell_style), Paragraph("Droplet VPS", table_cell_style), Paragraph("Infraestructura escalable con systemd y UFW.", table_cell_style)],
    ]

    t = Table(stack_data, colWidths=[1.1*inch, 1.3*inch, 1.4*inch, 3.6*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    # Section 2: Funcionalidades Críticas
    story.append(Paragraph("2. MÓDULOS Y CAPACIDADES DESTACADAS", h1_style))
    story.append(Paragraph("• <b>Doble Referencia GPS + Cámara Móvil:</b> Captura de coordenadas de alta exactitud satelital y fotografía real de la fachada del cliente almacenada en <font color='#0284c7'>/media/uploads/points/</font>.", body_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph("• <b>Prevención Matemática de Duplicados (&le; 50m):</b> Algoritmo de Haversine integrado en Django ORM que detecta puntos cercanos y ofrece actualizar el existente sin duplicar registros.", body_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph("• <b>Trazabilidad y Auditoría:</b> Autoría de repartidor, histórico inmutable de coordenadas y registro en tiempo real de operaciones en Cartagena.", body_style))
    story.append(Spacer(1, 10))

    # Section 3: Credenciales de Demostración
    story.append(Paragraph("3. CREDENCIALES DE ACCESO (DEMOSTRACIÓN)", h1_style))
    story.append(Spacer(1, 4))

    cred_data = [
        [Paragraph("Rol", table_header_style), Paragraph("Usuario", table_header_style), Paragraph("Contraseña", table_header_style), Paragraph("Acceso Principal", table_header_style)],
        [Paragraph("Super Admin (ROOT)", table_cell_bold), Paragraph("admin", table_cell_style), Paragraph("Admin123*", table_cell_style), Paragraph("http://127.0.0.1:8000/dashboard/", table_cell_style)],
        [Paragraph("Coordinador", table_cell_bold), Paragraph("coordinador", table_cell_style), Paragraph("Coord123*", table_cell_style), Paragraph("http://127.0.0.1:8000/coordinacion", table_cell_style)],
        [Paragraph("Repartidor 1 (J. Martínez)", table_cell_bold), Paragraph("repartidor1", table_cell_style), Paragraph("Driver123*", table_cell_style), Paragraph("http://127.0.0.1:8000/repartidor/ruta-activa/", table_cell_style)],
        [Paragraph("Repartidor 2 (S. Salgado)", table_cell_bold), Paragraph("repartidor2", table_cell_style), Paragraph("Driver123*", table_cell_style), Paragraph("http://127.0.0.1:8000/repartidor/ruta-activa/", table_cell_style)],
        [Paragraph("Repartidor 3 (J. Espinosa)", table_cell_bold), Paragraph("repartidor3", table_cell_style), Paragraph("Driver123*", table_cell_style), Paragraph("http://127.0.0.1:8000/repartidor/ruta-activa/", table_cell_style)],
        [Paragraph("Repartidor 4 (J. Amazan)", table_cell_bold), Paragraph("repartidor4", table_cell_style), Paragraph("Driver123*", table_cell_style), Paragraph("http://127.0.0.1:8000/repartidor/ruta-activa/", table_cell_style)],
        [Paragraph("Django Admin", table_cell_bold), Paragraph("admin", table_cell_style), Paragraph("Admin123*", table_cell_style), Paragraph("http://127.0.0.1:8000/admin/", table_cell_style)],
    ]

    t_cred = Table(cred_data, colWidths=[1.8*inch, 1.2*inch, 1.2*inch, 3.2*inch])
    t_cred.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t_cred)

    doc.build(story)

if __name__ == '__main__':
    root_pdf = 'STACK_TECNOLOGICO_GTR.pdf'
    media_dir = 'media'
    os.makedirs(media_dir, exist_ok=True)
    media_pdf = os.path.join(media_dir, 'STACK_TECNOLOGICO_GTR.pdf')
    
    create_pdf(root_pdf)
    create_pdf(media_pdf)
    print(f"PDF generado exitosamente en: {root_pdf} y {media_pdf}")
