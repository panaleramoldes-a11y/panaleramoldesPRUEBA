import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from fpdf import FPDF


def _txt_pdf(texto):
    """Sanitiza caracteres fuera de Latin-1 (como emojis) para evitar errores en fuentes estándar de FPDF."""
    if texto is None:
        return ""
    s = str(texto)
    reemplazos = {
        "’": "'", "‘": "'", "“": '"', "”": '"',
        "–": "-", "—": "-", "•": "-", "°": "°"
    }
    for k, v in reemplazos.items():
        s = s.replace(k, v)
    return s.encode("latin-1", "ignore").decode("latin-1")


def _fmt_moneda(valor):
    """Formatea números al estilo argentino ($ 1.250,00)."""
    val = float(valor or 0)
    txt = f"{val:,.2f}"
    txt = txt.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"${txt}"


def generar_pdf_presupuesto(datos):
    """Genera el PDF replicating el diseño corporativo adjunto y devuelve bytes."""
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    # Paleta de colores del diseño
    c_oscuro = (58, 58, 58)        # #3A3A3A Gris carbón
    c_dorado = (196, 160, 39)      # #C4A027 Dorado / Mostaza
    c_gris_texto = (110, 110, 110) # #6E6E6E Gris medio
    c_negro = (35, 35, 35)         # #232323 Texto principal
    c_fila_alt = (242, 242, 242)   # #F2F2F2 Fila alternada

    margen_izq = 18
    ancho_util = 174  # 210 - 18 - 18

    # ---------------------------------------------------------
    # 1. ENCABEZADO SUPERIOR (Bloque oscuro izq + Título der)
    # ---------------------------------------------------------
    pdf.set_fill_color(*c_oscuro)
    pdf.rect(margen_izq, 0, 74, 38, style="F")

    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_xy(margen_izq + 5, 12)
    pdf.cell(64, 7, _txt_pdf("PAÑALERA MOLDES"), align="C")

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(215, 215, 215)
    pdf.set_xy(margen_izq + 5, 20)
    pdf.cell(64, 5, _txt_pdf("ARTÍCULOS PARA BEBÉS Y NIÑOS"), align="C")

    # Título PRESUPUESTO a la derecha
    pdf.set_text_color(*c_negro)
    pdf.set_font("Helvetica", "B", 21)
    pdf.set_xy(105, 13)
    pdf.cell(87, 9, _txt_pdf("PRESUPUESTO"), align="R")

    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(*c_gris_texto)
    pdf.set_xy(105, 23)
    pdf.cell(87, 6, _txt_pdf(f"N° {datos['numero']}"), align="R")

    # ---------------------------------------------------------
    # 2. BLOQUE CLIENTE Y FECHAS
    # ---------------------------------------------------------
    y_cli = 48
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(*c_dorado)
    pdf.set_xy(margen_izq, y_cli)
    pdf.cell(95, 5, _txt_pdf("CLIENTE"))

    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(*c_negro)
    pdf.set_xy(margen_izq, y_cli + 5)
    pdf.cell(105, 7, _txt_pdf(datos["cliente_nombre"]))

    if datos.get("cliente_detalle"):
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(*c_gris_texto)
        pdf.set_xy(margen_izq, y_cli + 12.5)
        pdf.cell(105, 5, _txt_pdf(datos["cliente_detalle"]))

    # Fechas a la derecha
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(*c_negro)
    pdf.set_xy(125, y_cli + 5)
    pdf.cell(67, 5.5, _txt_pdf(f"Fecha: {datos['fecha_str']}"), align="R")

    pdf.set_xy(125, y_cli + 11)
    pdf.cell(67, 5.5, _txt_pdf(f"Vencimiento: {datos['vencimiento_str']}"), align="R")

    # ---------------------------------------------------------
    # 3. PERSONA DE CONTACTO Y DATOS DE PAGO
    # ---------------------------------------------------------
    y_cont = 72
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(*c_dorado)
    pdf.set_xy(margen_izq, y_cont)
    pdf.cell(90, 5, _txt_pdf("PERSONA DE CONTACTO"))

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*c_negro)
    tel_cli = datos.get("cliente_telefono") or "-"
    pdf.set_xy(margen_izq, y_cont + 5.5)
    pdf.cell(90, 5, _txt_pdf(f"Teléfono: {tel_cli}"))

    if datos.get("cliente_email"):
        pdf.set_xy(margen_izq, y_cont + 10.5)
        pdf.cell(90, 5, _txt_pdf(f"Email: {datos['cliente_email']}"))

    # Datos de pago a la derecha
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(*c_dorado)
    pdf.set_xy(115, y_cont)
    pdf.cell(77, 5, _txt_pdf("DATOS DE PAGO"), align="R")

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*c_negro)
    lineas_pago = [l.strip() for l in str(datos.get("datos_pago", "")).split("\n") if l.strip()]
    for idx_p, l_pago in enumerate(lineas_pago[:2]):
        pdf.set_xy(105, y_cont + 5.5 + (idx_p * 5))
        pdf.cell(87, 5, _txt_pdf(l_pago), align="R")

    # ---------------------------------------------------------
    # 4. TABLA DE ARTÍCULOS
    # ---------------------------------------------------------
    y_tabla = 95
    w_cols = [14, 84, 26, 22, 28]  # Suma = 174 mm
    headers = ["#", "DESCRIPCIÓN", "PRECIO", "CANTIDAD", "TOTAL"]

    # Cabecera oscura
    pdf.set_fill_color(*c_oscuro)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_xy(margen_izq, y_tabla)
    for w, h in zip(w_cols, headers):
        pdf.cell(w, 9, _txt_pdf(h), border=0, align="C", fill=True)

    y_actual = y_tabla + 9
    alto_fila = 8.5
    items = datos.get("items", [])

    for idx, item in enumerate(items, start=1):
        # Si hay muchos artículos y se acerca al pie, salta de página limpiamente
        if y_actual > 215:
            pdf.add_page()
            y_actual = 20
            pdf.set_fill_color(*c_oscuro)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Helvetica", "B", 8.5)
            pdf.set_xy(margen_izq, y_actual)
            for w, h in zip(w_cols, headers):
                pdf.cell(w, 9, _txt_pdf(h), border=0, align="C", fill=True)
            y_actual += 9

        es_par = (idx % 2 == 0)
        if es_par:
            pdf.set_fill_color(*c_fila_alt)
        else:
            pdf.set_fill_color(255, 255, 255)

        pdf.set_text_color(*c_negro)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_xy(margen_izq, y_actual)

        desc_corta = _txt_pdf(item.get("nombre", ""))[:46]
        precio_txt = _fmt_moneda(item.get("precio", 0))
        cant_txt = str(int(item.get("cantidad", 1)))
        sub_txt = _fmt_moneda(item.get("subtotal", 0))

        pdf.cell(w_cols[0], alto_fila, str(idx), align="C", fill=True)
        pdf.cell(w_cols[1], alto_fila, desc_corta, align="C", fill=True)
        pdf.cell(w_cols[2], alto_fila, precio_txt, align="C", fill=True)
        pdf.cell(w_cols[3], alto_fila, cant_txt, align="C", fill=True)
        pdf.cell(w_cols[4], alto_fila, sub_txt, align="C", fill=True)

        y_actual += alto_fila

    # Línea divisoria debajo de la tabla
    pdf.set_draw_color(180, 180, 180)
    pdf.line(margen_izq, y_actual, margen_izq + ancho_util, y_actual)
    y_post_tabla = y_actual + 4

    # ---------------------------------------------------------
    # 5. BLOQUE TOTALES (Derecha) + CONDICIONES / DETALLES (Izquierda)
    # ---------------------------------------------------------
    x_tot = margen_izq + w_cols[0] + w_cols[1]  # Alineado bajo columna PRECIO
    w_tot_lbl = w_cols[2] + w_cols[3]            # 48 mm
    w_tot_val = w_cols[4]                        # 28 mm

    y_tot = y_post_tabla
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(*c_negro)
    pdf.set_xy(x_tot, y_tot)
    pdf.cell(w_tot_lbl, 7, _txt_pdf("Subtotal"), align="C")
    pdf.cell(w_tot_val, 7, _fmt_moneda(datos["subtotal"]), align="C")
    y_tot += 7.5

    ajuste = float(datos.get("descuento_recargo", 0))
    if abs(ajuste) > 0.001:
        pdf.set_draw_color(160, 160, 160)
        pdf.line(x_tot, y_tot, x_tot + w_tot_lbl + w_tot_val, y_tot)
        lbl_ajuste = "Descuento" if ajuste < 0 else "Recargo / Envío"
        pdf.set_xy(x_tot, y_tot + 1)
        pdf.cell(w_tot_lbl, 7, _txt_pdf(lbl_ajuste), align="C")
        pdf.cell(w_tot_val, 7, _fmt_moneda(ajuste), align="C")
        y_tot += 8.5

    # Caja oscura de TOTAL
    pdf.set_fill_color(*c_oscuro)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_xy(x_tot, y_tot + 1)
    pdf.cell(w_tot_lbl, 8.5, _txt_pdf("TOTAL"), align="C", fill=True)
    pdf.cell(w_tot_val, 8.5, _fmt_moneda(datos["total"]), align="C", fill=True)

    # Textos legales/condiciones a la izquierda
    y_notas = max(y_post_tabla + 2, 185) if y_post_tabla < 185 else y_post_tabla + 2
    if y_notas > 225:
        y_notas = y_post_tabla + 2

    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(*c_dorado)
    pdf.set_xy(margen_izq, y_notas)
    pdf.cell(85, 5, _txt_pdf("CONDICIONES DE PAGO"))

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*c_negro)
    pdf.set_xy(margen_izq, y_notas + 5)
    pdf.multi_cell(82, 4, _txt_pdf(datos.get("condiciones_pago", "")))

    y_det = pdf.get_y() + 4
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(*c_dorado)
    pdf.set_xy(margen_izq, y_det)
    pdf.cell(85, 5, _txt_pdf("OTROS DETALLES"))

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*c_negro)
    pdf.set_xy(margen_izq, y_det + 5)
    pdf.multi_cell(82, 4, _txt_pdf(datos.get("otros_detalles", "")))

    # ---------------------------------------------------------
    # 6. FIRMA (Izquierda) Y PIE DE CONTACTO LOCAL (Derecha)
    # ---------------------------------------------------------
    y_pie = 252
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(*c_dorado)
    pdf.set_xy(margen_izq, y_pie)
    pdf.cell(65, 5, _txt_pdf("FIRMA"))

    pdf.set_draw_color(150, 150, 150)
    pdf.line(margen_izq, y_pie + 16, margen_izq + 62, y_pie + 16)

    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*c_negro)
    pdf.set_xy(margen_izq, y_pie + 17.5)
    pdf.cell(62, 5, _txt_pdf("Pañalera Moldes"))

    # Datos de contacto del local a la derecha + barra amarilla
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(*c_negro)
    pdf.set_xy(105, y_pie + 2)
    pdf.cell(87, 5, _txt_pdf("Mendoza 1797 - Salta Capital"), align="R")

    pdf.set_xy(105, y_pie + 7.5)
    pdf.cell(87, 5, _txt_pdf("WhatsApp: 3876300527"), align="R")

    # Barra dorada inferior derecha
    pdf.set_fill_color(*c_dorado)
    pdf.rect(105, y_pie + 15, 87, 7, style="F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_xy(105, y_pie + 15.8)
    pdf.cell(87, 5.5, _txt_pdf("PAÑALERA MOLDES - SALTA"), align="C")

    return bytes(pdf.output())


def render_modulo_presupuestos(db, nombre_usuario_actual="Administrador"):
    st.header("📄 Emisión de Presupuestos")
    st.caption("Armá cotizaciones sin descontar stock ni afectar la caja y descargá el PDF listo para enviar.")

    if "carrito_presupuesto" not in st.session_state:
        st.session_state.carrito_presupuesto = []
    if "ultimo_pdf_presupuesto" not in st.session_state:
        st.session_state.ultimo_pdf_presupuesto = None

    tab_nuevo, tab_hist = st.tabs(["➕ Nuevo Presupuesto", "📜 Historial Emitidos"])

    # ==========================================================================
    # PESTAÑA 1: NUEVO PRESUPUESTO (ESTILO POS)
    # ==========================================================================
    with tab_nuevo:
        try:
            res_prod = db.table("PRODUCTOS").select(
                "ID_Producto", "Nombre", "Marca", "Talle", "Stock_Actual",
                "Precio_1", "Precio_2", "Precio_3", "Precio_4", "Precio_5", "Estado"
            ).execute()
            df_prods = pd.DataFrame(res_prod.data) if (res_prod and res_prod.data) else pd.DataFrame()
            if not df_prods.empty and "Estado" in df_prods.columns:
                df_prods = df_prods[df_prods["Estado"].fillna("ACTIVO").str.upper() != "INACTIVO"]

            res_cli = db.table("CLIENTES").select("*").execute()
            df_cli = pd.DataFrame(res_cli.data) if (res_cli and res_cli.data) else pd.DataFrame()
        except Exception as e:
            st.error(f"Error cargando catálogo o clientes: {e}")
            return

        col_izq, col_der = st.columns([1.45, 1.15], gap="large")

        # ----------------------------------------------------------------------
        # COLUMNA IZQUIERDA: SELECCIÓN DE ARTÍCULOS Y CARRITO
        # ----------------------------------------------------------------------
        with col_izq:
            with st.container(border=True):
                st.markdown("#### 🛒 1. Selección de Artículos")

                c_lp, c_busq = st.columns([1, 2.2])
                lista_sel = c_lp.selectbox(
                    "Lista de Precios",
                    ["Precio_1", "Precio_2", "Precio_3", "Precio_4", "Precio_5"],
                    key="pres_lista_precio"
                )

                if not df_prods.empty:
                    df_prods["label_busqueda"] = df_prods.apply(
                        lambda r: f"{r['Nombre']} | Stock: {r.get('Stock_Actual', 0)} | {_fmt_moneda(r.get(lista_sel, 0))} (Cód: {r['ID_Producto']})",
                        axis=1
                    )
                    opciones_prod = df_prods["label_busqueda"].tolist()
                    prod_elegido = c_busq.selectbox(
                        "Buscar producto por nombre o código",
                        options=opciones_prod,
                        index=None,
                        placeholder="Escribí para buscar...",
                        key="pres_buscador_prod"
                    )

                    c_cant, c_punit, c_add = st.columns([1, 1.2, 1.2], vertical_alignment="bottom")
                    precio_sugerido = 0.0
                    fila_p = None
                    if prod_elegido:
                        fila_p = df_prods[df_prods["label_busqueda"] == prod_elegido].iloc[0]
                        precio_sugerido = float(fila_p.get(lista_sel) or 0.0)

                    cant_ing = c_cant.number_input("Cantidad", min_value=1, max_value=999, value=1, key="pres_cant_input")
                    precio_ing = c_punit.number_input(
                        "Precio Unit. ($)",
                        min_value=0.0,
                        value=precio_sugerido,
                        step=100.0,
                        key=f"pres_precio_input_{prod_elegido}_{lista_sel}"
                    )

                    if c_add.button("➕ Agregar", use_container_width=True, type="primary", disabled=(fila_p is None)):
                        id_p = str(fila_p["ID_Producto"])
                        nom_p = str(fila_p["Nombre"])
                        existente = next((x for x in st.session_state.carrito_presupuesto if x["id"] == id_p and abs(x["precio"] - precio_ing) < 0.01), None)
                        if existente:
                            existente["cantidad"] += int(cant_ing)
                            existente["subtotal"] = round(existente["cantidad"] * existente["precio"], 2)
                        else:
                            st.session_state.carrito_presupuesto.append({
                                "id": id_p,
                                "nombre": nom_p,
                                "cantidad": int(cant_ing),
                                "precio": float(precio_ing),
                                "subtotal": round(int(cant_ing) * float(precio_ing), 2)
                            })
                        st.rerun()

                # Opción para agregar ítem manual libre (ej: producto especial o envío)
                with st.expander("✏️ Agregar ítem manual (fuera de catálogo)"):
                    m1, m2, m3, m4 = st.columns([2.5, 1, 1.2, 1], vertical_alignment="bottom")
                    man_desc = m1.text_input("Descripción", key="pres_man_desc")
                    man_cant = m2.number_input("Cant.", min_value=1, value=1, key="pres_man_cant")
                    man_prec = m3.number_input("Precio ($)", min_value=0.0, step=100.0, key="pres_man_prec")
                    if m4.button("Sumar", key="pres_man_btn", use_container_width=True):
                        if man_desc.strip():
                            st.session_state.carrito_presupuesto.append({
                                "id": "MANUAL",
                                "nombre": man_desc.strip().upper(),
                                "cantidad": int(man_cant),
                                "precio": float(man_prec),
                                "subtotal": round(int(man_cant) * float(man_prec), 2)
                            })
                            st.rerun()

            # Detalle del carrito de presupuesto
            with st.container(border=True):
                c_tit, c_vac = st.columns([3, 1], vertical_alignment="center")
                c_tit.markdown("#### 📋 Detalle a Cotizar")
                if st.session_state.carrito_presupuesto:
                    if c_vac.button("🗑️ Vaciar", key="pres_vaciar", use_container_width=True):
                        st.session_state.carrito_presupuesto = []
                        st.rerun()

                if not st.session_state.carrito_presupuesto:
                    st.info("Todavía no agregaste artículos al presupuesto.")
                else:
                    for idx_c, item_c in enumerate(st.session_state.carrito_presupuesto):
                        col_n, col_q, col_pr, col_st, col_del = st.columns([2.8, 0.9, 1.2, 1.2, 0.6], vertical_alignment="center")
                        col_n.markdown(f"**{item_c['nombre']}**")

                        nueva_q = col_q.number_input(
                            "Cant", min_value=1, value=int(item_c["cantidad"]),
                            key=f"p_q_{idx_c}", label_visibility="collapsed"
                        )
                        nuevo_pr = col_pr.number_input(
                            "Precio", min_value=0.0, value=float(item_c["precio"]), step=50.0,
                            key=f"p_pr_{idx_c}", label_visibility="collapsed"
                        )

                        if nueva_q != item_c["cantidad"] or abs(nuevo_pr - item_c["precio"]) > 0.001:
                            st.session_state.carrito_presupuesto[idx_c]["cantidad"] = int(nueva_q)
                            st.session_state.carrito_presupuesto[idx_c]["precio"] = float(nuevo_pr)
                            st.session_state.carrito_presupuesto[idx_c]["subtotal"] = round(int(nueva_q) * float(nuevo_pr), 2)
                            st.rerun()

                        col_st.markdown(f"**{_fmt_moneda(item_c['subtotal'])}**")
                        if col_del.button("✖", key=f"p_del_{idx_c}"):
                            st.session_state.carrito_presupuesto.pop(idx_c)
                            st.rerun()

        # ----------------------------------------------------------------------
        # COLUMNA DERECHA: DATOS DEL CLIENTE, CONDICIONES Y EMISIÓN PDF
        # ----------------------------------------------------------------------
        with col_der:
            with st.container(border=True):
                st.markdown("#### 👤 2. Datos del Cliente y Condiciones")

                modo_cli = st.radio(
                    "Cliente:",
                    ["Seleccionar de Base de Clientes", "Escribir Cliente Eventual"],
                    horizontal=True,
                    key="pres_modo_cli"
                )

                id_cli_sel = None
                cli_nombre_def = ""
                cli_detalle_def = ""
                cli_tel_def = ""

                if modo_cli == "Seleccionar de Base de Clientes" and not df_cli.empty:
                    df_cli["label_cli"] = df_cli.apply(
                        lambda r: f"{str(r.get('Nombre') or '').strip()} {str(r.get('Apellido') or '').strip()} {str(r.get('Razón Social') or '').strip()} (ID: {r['ID_Cliente']})".strip(),
                        axis=1
                    )
                    cli_elegido = st.selectbox(
                        "Buscar cliente",
                        options=df_cli["label_cli"].tolist(),
                        index=None,
                        placeholder="Elegí un cliente...",
                        key="pres_select_cli"
                    )
                    if cli_elegido:
                        r_cli = df_cli[df_cli["label_cli"] == cli_elegido].iloc[0]
                        id_cli_sel = int(r_cli["ID_Cliente"])
                        nom_c = f"{str(r_cli.get('Nombre') or '').strip()} {str(r_cli.get('Apellido') or '').strip()}".strip()
                        rz_c = str(r_cli.get("Razón Social") or "").strip()
                        cli_nombre_def = nom_c if nom_c else rz_c
                        dir_c = str(r_cli.get("Direccion_1") or "").strip()
                        zona_c = str(r_cli.get("Zona") or "").strip()
                        cli_detalle_def = f"{dir_c} ({zona_c})" if (dir_c and zona_c) else (dir_c or rz_c)
                        cli_tel_def = str(r_cli.get("Telefono") or "").replace(".0", "").strip()

                cli_nombre = st.text_input("Nombre / Razón Social *", value=cli_nombre_def, key="pres_inp_nombre")
                c_d1, c_d2 = st.columns(2)
                cli_detalle = c_d1.text_input("Subtítulo / Dirección / Empresa", value=cli_detalle_def, key="pres_inp_det")
                cli_tel = c_d2.text_input("Teléfono de contacto", value=cli_tel_def, key="pres_inp_tel")
                cli_email = st.text_input("Email (Opcional)", value="", key="pres_inp_email")

                c_f1, c_f2 = st.columns(2)
                dias_validez = c_f1.number_input("Validez (días)", min_value=1, max_value=60, value=7, key="pres_dias_val")
                ajuste_monto = c_f2.number_input(
                    "Descuento (-) / Envío (+) ($)",
                    value=0.0,
                    step=100.0,
                    help="Usá valor negativo (ej. -1500) para aplicar un descuento.",
                    key="pres_ajuste"
                )

                with st.expander("⚙️ Textos de Pago y Condiciones del PDF", expanded=False):
                    datos_pago_txt = st.text_area(
                        "Datos de Pago (bloque superior derecho):",
                        value="Efectivo / Transferencia / Tarjetas\nPañalera Moldes",
                        height=68,
                        key="pres_datos_pago"
                    )
                    cond_pago_txt = st.text_area(
                        "Condiciones de Pago:",
                        value="Los precios expresados son finales e incluyen IVA. Presupuesto válido hasta la fecha de vencimiento indicada, sujeto a disponibilidad de stock.",
                        height=75,
                        key="pres_cond_pago"
                    )
                    otros_det_txt = st.text_area(
                        "Otros Detalles:",
                        value="Consultá por envíos a domicilio en Salta Capital. Para confirmar el pedido, comunicate por WhatsApp.",
                        height=68,
                        key="pres_otros_det"
                    )

                # Cálculo de totales
                subtotal_pres = round(sum(x["subtotal"] for x in st.session_state.carrito_presupuesto), 2)
                total_pres = round(subtotal_pres + float(ajuste_monto), 2)

                st.divider()
                st.markdown(f"### Total Presupuestado: **{_fmt_moneda(total_pres)}**")

                if st.button("📄 EMITIR PRESUPUESTO", type="primary", use_container_width=True):
                    if not st.session_state.carrito_presupuesto:
                        st.warning("⚠️ Agregá al menos un producto antes de emitir el presupuesto.")
                    elif not cli_nombre.strip():
                        st.warning("⚠️ Ingresá el nombre del cliente.")
                    else:
                        try:
                            ahora = datetime.now()
                            venc = ahora + timedelta(days=int(dias_validez))

                            payload_db = {
                                "Fecha": ahora.isoformat(),
                                "Fecha_Vencimiento": venc.strftime("%Y-%m-%d"),
                                "ID_Cliente": id_cli_sel,
                                "Cliente_Nombre": cli_nombre.strip().upper(),
                                "Cliente_Detalle": cli_detalle.strip(),
                                "Cliente_Telefono": cli_tel.strip(),
                                "Cliente_Email": cli_email.strip(),
                                "Lista_Precio": lista_sel,
                                "Items_JSON": st.session_state.carrito_presupuesto,
                                "Subtotal": subtotal_pres,
                                "Descuento_Recargo": float(ajuste_monto),
                                "Total": total_pres,
                                "Datos_Pago": datos_pago_txt.strip(),
                                "Condiciones_Pago": cond_pago_txt.strip(),
                                "Otros_Detalles": otros_det_txt.strip(),
                                "Usuario_Emisor": str(nombre_usuario_actual)
                            }

                            res_ins = db.table("PRESUPUESTOS").insert(payload_db).execute()
                            nuevo_id = res_ins.data[0]["ID_Presupuesto"]
                            num_formateado = f"001-{int(nuevo_id):06d}"

                            db.table("PRESUPUESTOS").update(
                                {"Numero_Formateado": num_formateado}
                            ).eq("ID_Presupuesto", nuevo_id).execute()

                            datos_pdf = {
                                "numero": num_formateado,
                                "fecha_str": ahora.strftime("%d/%m/%Y"),
                                "vencimiento_str": venc.strftime("%d/%m/%Y"),
                                "cliente_nombre": cli_nombre.strip().upper(),
                                "cliente_detalle": cli_detalle.strip(),
                                "cliente_telefono": cli_tel.strip(),
                                "cliente_email": cli_email.strip(),
                                "datos_pago": datos_pago_txt.strip(),
                                "condiciones_pago": cond_pago_txt.strip(),
                                "otros_detalles": otros_det_txt.strip(),
                                "items": st.session_state.carrito_presupuesto,
                                "subtotal": subtotal_pres,
                                "descuento_recargo": float(ajuste_monto),
                                "total": total_pres
                            }

                            pdf_bytes = generar_pdf_presupuesto(datos_pdf)
                            st.session_state.ultimo_pdf_presupuesto = {
                                "bytes": pdf_bytes,
                                "filename": f"Presupuesto_{num_formateado}_{cli_nombre.strip().replace(' ', '_')}.pdf",
                                "numero": num_formateado
                            }
                            st.success(f"✅ Presupuesto **N° {num_formateado}** generado correctamente (sin descontar stock ni caja).")

                        except Exception as e_em:
                            st.error(f"Error al emitir el presupuesto: {e_em}")

                # Botón de descarga visible inmediatamente tras emitir
                if st.session_state.ultimo_pdf_presupuesto:
                    st.download_button(
                        label=f"📥 Descargar PDF (N° {st.session_state.ultimo_pdf_presupuesto['numero']})",
                        data=st.session_state.ultimo_pdf_presupuesto["bytes"],
                        file_name=st.session_state.ultimo_pdf_presupuesto["filename"],
                        mime="application/pdf",
                        type="secondary",
                        use_container_width=True
                    )

    # ==========================================================================
    # PESTAÑA 2: HISTORIAL DE PRESUPUESTOS EMITIDOS
    # ==========================================================================
    with tab_hist:
        try:
            res_h = db.table("PRESUPUESTOS").select("*").order("ID_Presupuesto", desc=True).limit(50).execute()
            df_h = pd.DataFrame(res_h.data) if (res_h and res_h.data) else pd.DataFrame()

            if df_h.empty:
                st.info("Todavía no hay presupuestos emitidos.")
            else:
                busq_h = st.text_input("Buscar por cliente o número:", key="pres_busq_hist")
                if busq_h.strip():
                    mask = (
                        df_h["Cliente_Nombre"].fillna("").str.contains(busq_h, case=False) |
                        df_h["Numero_Formateado"].fillna("").str.contains(busq_h, case=False)
                    )
                    df_h = df_h[mask]

                for _, r_h in df_h.iterrows():
                    num_h = r_h.get("Numero_Formateado") or f"001-{int(r_h['ID_Presupuesto']):06d}"
                    fecha_h = pd.to_datetime(r_h["Fecha"]).strftime("%d/%m/%Y") if pd.notnull(r_h.get("Fecha")) else "-"
                    venc_h = pd.to_datetime(r_h["Fecha_Vencimiento"]).strftime("%d/%m/%Y") if pd.notnull(r_h.get("Fecha_Vencimiento")) else "-"

                    with st.container(border=True):
                        ch1, ch2, ch3 = st.columns([2.5, 1.5, 1.2], vertical_alignment="center")
                        ch1.markdown(f"**N° {num_h}** — {r_h['Cliente_Nombre']}")
                        ch1.caption(f"Emitido: {fecha_h} | Vence: {venc_h} | Lista: {r_h.get('Lista_Precio', '-')}")
                        ch2.markdown(f"**{_fmt_moneda(r_h.get('Total', 0))}**")
                        ch2.caption(f"{len(r_h.get('Items_JSON') or [])} ítems")

                        datos_reimp = {
                            "numero": num_h,
                            "fecha_str": fecha_h,
                            "vencimiento_str": venc_h,
                            "cliente_nombre": r_h.get("Cliente_Nombre", ""),
                            "cliente_detalle": r_h.get("Cliente_Detalle", ""),
                            "cliente_telefono": r_h.get("Cliente_Telefono", ""),
                            "cliente_email": r_h.get("Cliente_Email", ""),
                            "datos_pago": r_h.get("Datos_Pago", ""),
                            "condiciones_pago": r_h.get("Condiciones_Pago", ""),
                            "otros_detalles": r_h.get("Otros_Detalles", ""),
                            "items": r_h.get("Items_JSON") or [],
                            "subtotal": float(r_h.get("Subtotal") or 0),
                            "descuento_recargo": float(r_h.get("Descuento_Recargo") or 0),
                            "total": float(r_h.get("Total") or 0)
                        }
                        pdf_reimp = generar_pdf_presupuesto(datos_reimp)
                        ch3.download_button(
                            label="📥 PDF",
                            data=pdf_reimp,
                            file_name=f"Presupuesto_{num_h}.pdf",
                            mime="application/pdf",
                            key=f"reimp_{r_h['ID_Presupuesto']}",
                            use_container_width=True
                        )
        except Exception as e_h:
            st.error(f"Error al cargar historial: {e_h}")
