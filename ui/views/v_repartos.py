"""
ui/views/v_repartos.py
Vista principal para la planificación y visualización de rutas de reparto.
"""

import pandas as pd
import streamlit as st
from services.delivery_service import (
    cargar_puntos_reparto,
    extraer_coords_desde_link,
    obtener_ventas_reparto,
)
from services.routing_service import optimizar_ruta


def render_repartos_view():
    puntos_db = cargar_puntos_reparto()
    ventas_reparto = obtener_ventas_reparto()

    if not ventas_reparto:
        st.info("No hay repartos pendientes.")
        return

    df = pd.DataFrame(ventas_reparto)
    df["Fecha_Entrega"] = pd.to_datetime(df["Fecha_Entrega"]).dt.date
    df = df.sort_values(by="Fecha_Entrega")

    total_general = len(df)
    st.markdown(f"## 🗺️ Planificación de Repartos ({total_general})")
    st.divider()

    rol_usuario = st.session_state.get("rol", "Vendedor")

    for fecha, grupo in df.groupby("Fecha_Entrega"):
        st.subheader(f"📅 {fecha} ({len(grupo)})")

        punto_partida = None
        punto_llegada = None

        if rol_usuario == "Administrador":
            with st.expander(f"⚙️ Configurar Origen y Destino para {fecha}"):
                c_origen, c_destino = st.columns(2)

                # --- CONFIGURACIÓN ORIGEN ---
                with c_origen:
                    st.markdown("**📍 Punto de Partida**")
                    opciones_origen = {**puntos_db, "Otro (Link de Maps)": "link"}

                    sel_origen = st.selectbox(
                        "¿Desde dónde sale el reparto?",
                        list(opciones_origen.keys()),
                        key=f"sel_orig_{fecha}",
                    )

                    if sel_origen == "Otro (Link de Maps)":
                        link_orig = st.text_input(
                            "Pega el link de origen:", key=f"link_orig_{fecha}"
                        )
                        if link_orig:
                            coords_orig = extraer_coords_desde_link(link_orig)
                            if coords_orig:
                                st.success(f"Origen detectado: {coords_orig}")
                                punto_partida = coords_orig
                            else:
                                st.error(
                                    "No se pudo leer el link. Se usará el primer punto por defecto."
                                )
                                punto_partida = (
                                    list(puntos_db.values())[0]
                                    if puntos_db
                                    else None
                                )
                        else:
                            punto_partida = (
                                list(puntos_db.values())[0]
                                if puntos_db
                                else None
                            )
                    else:
                        punto_partida = opciones_origen[sel_origen]

                # --- CONFIGURACIÓN DESTINO FINAL ---
                with c_destino:
                    st.markdown("**🏁 Punto de Finalización**")
                    opciones_destino = {**puntos_db, "Otro (Link de Maps)": "link"}

                    nombre_defecto = (
                        list(puntos_db.keys())[0]
                        if puntos_db
                        else "Punto Principal"
                    )
                    coords_defecto = (
                        list(puntos_db.values())[0] if puntos_db else None
                    )

                    sel_destino = st.selectbox(
                        "¿Dónde termina la ruta?",
                        list(opciones_destino.keys()),
                        index=0,
                        key=f"sel_dest_{fecha}",
                    )

                    if sel_destino == "Otro (Link de Maps)":
                        link_dest = st.text_input(
                            "Pega el link de destino:", key=f"link_dest_{fecha}"
                        )
                        if link_dest:
                            coords_dest = extraer_coords_desde_link(link_dest)
                            if coords_dest:
                                st.success(f"Destino detectado: {coords_dest}")
                                punto_llegada = coords_dest
                            else:
                                st.error(
                                    f"No se pudo leer el link. Se usará {nombre_defecto} por defecto."
                                )
                                punto_llegada = coords_defecto
                        else:
                            punto_llegada = coords_defecto
                    else:
                        punto_llegada = opciones_destino[sel_destino]

            # Botón de optimización con OR-Tools
            if st.button(
                f"🚀 Generar Ruta Optimizada para {fecha}",
                key=f"btn_{fecha}",
            ):
                st.session_state[f"mostrar_diagrama_{fecha}"] = True
                st.session_state[f"p_partida_{fecha}"] = punto_partida
                st.session_state[f"p_llegada_{fecha}"] = punto_llegada

            if st.session_state.get(f"mostrar_diagrama_{fecha}", False):
                p_partida = st.session_state.get(f"p_partida_{fecha}", punto_partida)
                p_llegada = st.session_state.get(f"p_llegada_{fecha}", punto_llegada)

                # Convertimos filas del grupo en una lista de paradas
                destinos = []
                for _, row in grupo.iterrows():
                    link = row.get("Link_Maps_Entrega", "")
                    coords = extraer_coords_desde_link(link)
                    destinos.append({
                        "cliente": row["Cliente"],
                        "direccion": row["Direccion_Entrega"],
                        "coords": coords or p_partida,
                    })

                if p_partida:
                    ruta_ordenada = optimizar_ruta(
                        origen=p_partida,
                        destinos=destinos,
                        destino_final=p_llegada,
                    )

                    st.success("✅ Ruta calculada exitosamente.")
                    st.markdown("**Orden de visita optimizado:**")
                    for i, parada in enumerate(ruta_ordenada, 1):
                        st.write(f"**{i}.** {parada['cliente']} — {parada['direccion']}")

        # Listado de tarjetas de entrega
        for _, v in grupo.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 2, 1])
                c1.write(f"👤 **Cliente:** {v['Cliente']}")
                c2.write(f"📍 **Dir:** {v['Direccion_Entrega']}")

                if v.get("Link_Maps_Entrega"):
                    c3.link_button("📍 Maps", v["Link_Maps_Entrega"])

                obs_entrega = v.get("Observaciones", "")
                if (
                    pd.notna(obs_entrega)
                    and str(obs_entrega).strip()
                    and str(obs_entrega).strip().lower() not in ["nan", "none"]
                ):
                    st.info(
                        f"📝 **Nota para el repartidor:** {obs_entrega}",
                        icon="📌",
                    )

                st.caption(f"💰 {v['Metodo_Pago']}")
