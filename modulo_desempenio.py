import streamlit as st
import pandas as pd
from datetime import datetime, time

def render_modulo_desempenio(db):
    st.title("🛡️ Gestión de Desempeño y Tareas Diarias")
    
    tab_checklist, tab_bono, tab_historial = st.tabs([
        "📋 Checklist Diario", 
        "🏆 Bono de Excelencia", 
        "📊 Historial & Auditoría"
    ])

    # -----------------------------------------------------------------
    # PESTAÑA 1: CHECKLIST DIARIO DE TAREAS
    # -----------------------------------------------------------------
    with tab_checklist:
        st.subheader("📋 Registro Operativo Diario")
        st.caption("Completá los horarios de ejecución, estado y novedades de cada tarea asignada a la jornada.")

        col_f1, col_f2 = st.columns([1, 2])
        fecha_sel = col_f1.date_input("Fecha de Trabajo", value=datetime.now().date(), key="chk_fecha_sel")
        usuario_actual = st.session_state.get("usuario", "Vendedora")

        # Cargar tareas guardadas para esta fecha
        res_existente = db.table("REGISTRO_TAREAS_DIARIAS").select("*").eq("fecha", str(fecha_sel)).execute().data or []

        if not res_existente:
            # Si no hay registros aún, cargamos las plantillas
            res_plantilla = db.table("TAREAS_PLANTILLA").select("*").eq("activo", True).order("orden").execute().data or []
            tareas_mostrar = []
            for t in res_plantilla:
                tareas_mostrar.append({
                    "id": None,
                    "nombre_tarea": t["nombre_tarea"],
                    "horario_sugerido": t.get("horario_sugerido", ""),
                    "hora_inicio": time(14, 0),
                    "hora_fin": time(14, 15),
                    "estado": "PENDIENTE",
                    "observaciones": ""
                })
        else:
            tareas_mostrar = []
            for r in res_existente:
                h_ini = datetime.strptime(r["hora_inicio"], "%H:%M:%S").time() if r.get("hora_inicio") else time(14, 0)
                h_fin = datetime.strptime(r["hora_fin"], "%H:%M:%S").time() if r.get("hora_fin") else time(14, 15)
                tareas_mostrar.append({
                    "id": r["id"],
                    "nombre_tarea": r["nombre_tarea"],
                    "horario_sugerido": r.get("horario_sugerido", ""),
                    "hora_inicio": h_ini,
                    "hora_fin": h_fin,
                    "estado": r.get("estado", "PENDIENTE"),
                    "observaciones": r.get("observaciones", "") or ""
                })

        st.divider()

        # Formulario de carga interactivo
        with st.form(key="form_checklist_diario"):
            registros_para_guardar = []

            for idx, item in enumerate(tareas_mostrar):
                st.markdown(f"##### 📌 {item['nombre_tarea']}")
                if item['horario_sugerido']:
                    st.caption(f"Horario Sugerido: {item['horario_sugerido']}")

                c1, c2, c3, c4 = st.columns([1, 1, 1.2, 2.5])
                
                h_inicio = c1.time_input("Inicio Real", value=item['hora_inicio'], key=f"h_ini_{idx}")
                h_fin = c2.time_input("Fin Real", value=item['hora_fin'], key=f"h_fin_{idx}")
                
                opts_estado = ["PENDIENTE", "✅ CUMPLIDA", "⚠️ PARCIAL", "❌ NO REALIZADA"]
                idx_est = opts_estado.index(item['estado']) if item['estado'] in opts_estado else 0
                est_sel = c3.selectbox("Estado", opts_estado, index=idx_est, key=f"est_{idx}")
                
                obs_val = c4.text_input("Observaciones / Novedad", value=item['observaciones'], placeholder="Ej: No se terminó por alta demanda en caja", key=f"obs_{idx}")

                registros_para_guardar.append({
                    "id": item["id"],
                    "fecha": str(fecha_sel),
                    "usuario": usuario_actual,
                    "nombre_tarea": item["nombre_tarea"],
                    "horario_sugerido": item["horario_sugerido"],
                    "hora_inicio": str(h_inicio),
                    "hora_fin": str(h_fin),
                    "estado": est_sel,
                    "observaciones": obs_val
                })
                st.markdown("---")

            btn_guardar_chk = st.form_submit_button("💾 Guardar Checklist Diario", type="primary", use_container_width=True)

            if btn_guardar_chk:
                try:
                    for reg in registros_para_guardar:
                        payload = {
                            "fecha": reg["fecha"],
                            "usuario": reg["usuario"],
                            "nombre_tarea": reg["nombre_tarea"],
                            "horario_sugerido": reg["horario_sugerido"],
                            "hora_inicio": reg["hora_inicio"],
                            "hora_fin": reg["hora_fin"],
                            "estado": reg["estado"],
                            "observaciones": reg["observaciones"]
                        }
                        if reg["id"]:
                            db.table("REGISTRO_TAREAS_DIARIAS").update(payload).eq("id", reg["id"]).execute()
                        else:
                            db.table("REGISTRO_TAREAS_DIARIAS").insert(payload).execute()
                    
                    st.success("✅ ¡Checklist de la jornada guardado correctamente!")
                    st.rerun()  # <--- HACE EL REFRESH EN TIEMPO REAL
                except Exception as e:
                    st.error(f"❌ Error al guardar checklist: {e}")

    # -----------------------------------------------------------------
    # PESTAÑA 2: BONO DE EXCELENCIA & PUNTAJE
    # -----------------------------------------------------------------
    with tab_bono:
        st.subheader("🏆 Control y Seguimiento del Bono de Excelencia")
        
        mes_activo = datetime.now().strftime("%Y-%m")
        st.info(f"📅 **Periodo Activo:** {datetime.now().strftime('%B %Y').title()} (`{mes_activo}`)")

        # Cargar puntos acumulados del mes
        res_puntos = db.table("PUNTOS_BONO_EXCELENCIA").select("*").eq("mes_anio", mes_activo).execute().data or []
        
        puntos_base = 100
        ajuste_puntos = sum([p["puntos"] for p in res_puntos])
        total_puntos = puntos_base + ajuste_puntos

        # KPIs Visuales
        k1, k2, k3 = st.columns(3)
        k1.metric("💯 Puntos Base", f"{puntos_base} pts")
        k2.metric("📊 Ajuste acumulado", f"{ajuste_puntos:+d} pts")
        k3.metric("🎯 PUNTAJE ACTUAL", f"{total_puntos} pts")

        # Escala de Recompensas
        if total_puntos >= 90:
            st.success("🏆 **Escalón Alcanzado:** $100.000 (Bono Sobresaliente 100%)")
        elif total_puntos >= 80:
            st.info("🥇 **Escalón Alcanzado:** $75.000 (Bono Alto)")
        elif total_puntos >= 60:
            st.warning("🥈 **Escalón Alcanzado:** $50.000 (Mínimo Aceptable)")
        else:
            st.error("🚨 **Escalón Actual:** $0 (Sin Bono + Requiere Capacitación)")

        st.divider()

        # Registro de Novedades del Bono (Solo Admin o Encargada)
        if st.session_state.get('rol') == "Administrador":
            st.markdown("##### ➕ Registrar Ajuste de Puntos")
            
            with st.form("form_bono_puntos"):
                f_col1, f_col2 = st.columns([1, 2])
                
                tipo_evt = f_col1.selectbox("Tipo de Evento", [
                    "🎁 +10 PTS: Propuesta de Contenido (Scouting)",
                    "🎁 +5 PTS: Semana Perfecta (100% Checklists)",
                    "⚠️ -5 PTS: Orden e Imagen (Basura, Microzona, etc.)",
                    "⚠️ -10 PTS: Fallas Operativas (Quiebre stock, etc.)",
                    "❌ -25 PTS: Falta Crítica (Circuito de oro, Error envío, etc.)",
                    "⚙️ Ajuste Manual Personalizado"
                ])
                
                motivo_evt = f_col2.text_input("Motivo / Detalle de la novedad", placeholder="Ej: Error en pedido Tomas Garavaglia")
                pts_custom = f_col1.number_input("Puntos a aplicar (si es manual)", value=0, step=1)
                
                btn_reg_pts = st.form_submit_button("📌 Registrar Evento en el Bono", type="primary")

                if btn_reg_pts:
                    # Determinar puntos según selección
                    if "Propuesta de Contenido" in tipo_evt:
                        pts = 10
                    elif "Semana Perfecta" in tipo_evt:
                        pts = 5
                    elif "Orden e Imagen" in tipo_evt:
                        pts = -5
                    elif "Fallas Operativas" in tipo_evt:
                        pts = -10
                    elif "Falta Crítica" in tipo_evt:
                        pts = -25
                    else:
                        pts = int(pts_custom)

                    if not motivo_evt:
                        st.warning("⚠️ Debes ingresar un motivo.")
                    else:
                        payload_bono = {
                            "fecha": str(datetime.now().date()),
                            "mes_anio": mes_activo,
                            "usuario": st.session_state.get("usuario", "Vendedora"),
                            "tipo_evento": tipo_evt.split(":")[0],
                            "puntos": pts,
                            "motivo": motivo_evt,
                            "registrado_por": st.session_state.get("usuario", "Admin")
                        }
                        db.table("PUNTOS_BONO_EXCELENCIA").insert(payload_bono).execute()
                        st.success("✅ Novedad registrada en el historial del Bono.")
                        st.rerun()

        # Tabla del Historial del Mes
        st.markdown("##### 📜 Novedades Aplicadas en el Mes")
        if res_puntos:
            df_pts = pd.DataFrame(res_puntos)[["fecha", "tipo_evento", "puntos", "motivo", "registrado_por"]]
            st.dataframe(df_pts, use_container_width=True, hide_index=True)
        else:
            st.info("Sin faltas ni premios registrados en lo que va del mes. ¡Puntaje intacto! 👏")

    # -----------------------------------------------------------------
    # PESTAÑA 3: HISTORIAL & AUDITORÍA
    # -----------------------------------------------------------------
    with tab_historial:
        st.subheader("📊 Historial General y Auditoría")
        
        c_h1, c_h2 = st.columns(2)
        f_desde = c_h1.date_input("Desde", value=datetime.now().date().replace(day=1))
        f_hasta = c_h2.date_input("Hasta", value=datetime.now().date())

        res_audit = db.table("REGISTRO_TAREAS_DIARIAS")\
            .select("*")\
            .gte("fecha", str(f_desde))\
            .lte("fecha", str(f_hasta))\
            .execute().data or []

        if res_audit:
            df_audit = pd.DataFrame(res_audit)
            st.dataframe(df_audit[['fecha', 'usuario', 'nombre_tarea', 'hora_inicio', 'hora_fin', 'estado', 'observaciones']], use_container_width=True, hide_index=True)
        else:
            st.info("No se encontraron registros de tareas en el rango de fechas seleccionado.")
