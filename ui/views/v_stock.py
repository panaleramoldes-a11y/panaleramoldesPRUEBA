import io
import pandas as pd
import streamlit as st
from services import stock_service

def render():
    st.header("📊 Gestión y Análisis de Stock")

    # Carga base de datos de productos y proveedores
    try:
        df_prod, df_prov = stock_service.obtener_datos_stock()
    except Exception as e:
        st.error(str(e))
        return

    if df_prod.empty:
        st.info("No hay productos registrados en la base de datos.")
        return

    # Definición de pestañas
    tab_listado, tab_priorizacion = st.tabs([
        "📋 Listado y Buscador General", 
        "🎯 Priorización de Compras (ABC + Urgencia)"
    ])

    # -----------------------------------------------------------------
    # PESTAÑA 1: LISTADO Y BUSCADOR GENERAL
    # -----------------------------------------------------------------
    with tab_listado:
        st.subheader("🔍 Buscar Artículos")
        
        mostrar_inactivos = st.checkbox("👁️ Mostrar productos INACTIVOS", value=False, key="chk_inactivos_stock")
        
        busqueda_texto = st.text_input(
            "Escriba para filtrar por nombre o código:", 
            placeholder="Ej: babydry, pampers, 779...",
            key="busqueda_stock"
        )
        
        c1, c2, c3 = st.columns(3)
        rubros = ["Todos"] + [r for r in df_prod['Rubro'].dropna().unique().tolist() if r] if 'Rubro' in df_prod.columns else ["Todos"]
        marcas = ["Todos"] + [m for m in df_prod['Marca'].dropna().unique().tolist() if m] if 'Marca' in df_prod.columns else ["Todos"]
        provs = ["Todos"] + [p for p in df_prov['Razon_Social'].dropna().unique().tolist() if p] if not df_prov.empty and 'Razon_Social' in df_prov.columns else ["Todos"]
        
        filtro_rubro = c1.selectbox("Filtrar por Rubro", rubros, key="filtro_rubro_stock")
        filtro_marca = c2.selectbox("Filtrar por Marca", marcas, key="filtro_marca_stock")
        filtro_prov = c3.selectbox("Filtrar por Proveedor", provs, key="filtro_prov_stock")
        
        df_f = df_prod.copy()
        
        if 'Estado' in df_f.columns and not mostrar_inactivos:
            df_f = df_f[df_f['Estado'] != 'INACTIVO']

        if busqueda_texto:
            busqueda_texto = busqueda_texto.lower()
            mask = df_f['Nombre'].str.lower().str.contains(busqueda_texto, na=False) | \
                   df_f['ID_Producto'].astype(str).str.lower().str.contains(busqueda_texto, na=False)
            df_f = df_f[mask]
        
        if filtro_rubro != "Todos":
            df_f = df_f[df_f['Rubro'] == filtro_rubro]
            
        if filtro_marca != "Todos":
            df_f = df_f[df_f['Marca'] == filtro_marca]
            
        if filtro_prov != "Todos":
            if 'Proveedor' in df_f.columns:
                df_f = df_f[df_f['Proveedor'] == filtro_prov]
            elif 'ID_Proveedor' in df_f.columns and not df_prov.empty:
                prov_sel = df_prov[df_prov['Razon_Social'] == filtro_prov]
                if not prov_sel.empty:
                    id_prov_buscado = prov_sel.iloc[0]['ID_Proveedor']
                    df_f = df_f[df_f['ID_Proveedor'] == id_prov_buscado]
        
        df_f['Stock_Actual'] = pd.to_numeric(df_f['Stock_Actual'], errors='coerce').fillna(0)
        df_f['Stock_Min'] = pd.to_numeric(df_f['Stock_Min'], errors='coerce').fillna(0)
        df_f['Stock_Max'] = pd.to_numeric(df_f['Stock_Max'], errors='coerce').fillna(0)

        df_f['Faltante_Min'] = (df_f['Stock_Min'] - df_f['Stock_Actual']).clip(lower=0)
        df_f['Faltante_Max'] = (df_f['Stock_Max'] - df_f['Stock_Actual']).clip(lower=0)
        
        df_f['Pedir'] = False
        cols_mostrar = ['Pedir', 'Nombre', 'Stock_Actual', 'Stock_Min', 'Stock_Max', 'Faltante_Min', 'Faltante_Max']
        cols_presentes = [c for c in cols_mostrar if c in df_f.columns]

        st.caption("💡 Tildá únicamente los artículos que querés incluir en el mensaje de WhatsApp.")

        df_editado = st.data_editor(
            df_f[cols_presentes],
            column_config={
                "Pedir": st.column_config.CheckboxColumn(
                    "📱 Pedir",
                    help="Marcar para incluir en el mensaje de WhatsApp",
                    default=False
                )
            },
            disabled=['Nombre', 'Stock_Actual', 'Stock_Min', 'Stock_Max', 'Faltante_Min', 'Faltante_Max'],
            hide_index=True,
            use_container_width=True,
            key="editor_tabla_stock"
        )

        col_exp1, col_exp2 = st.columns(2)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_f.drop(columns=['Pedir'], errors='ignore').to_excel(writer, index=False)
        
        col_exp1.download_button(
            label="📥 Exportar a Excel", 
            data=buffer.getvalue(), 
            file_name="reporte_stock.xlsx", 
            mime="application/vnd.ms-excel"
        )
        
        if col_exp2.button("💬 Generar Resumen para WhatsApp", key="btn_wsp_p1"):
            seleccionados = df_editado[df_editado['Pedir'] == True]
            
            if seleccionados.empty:
                st.warning("⚠️ No has tildado ningún producto en la columna '📱 Pedir'. Seleccioná al menos uno en la tabla.")
            else:
                mensaje = "🛒 *Pedido Sugerido (Faltantes a Mínimo):*\n"
                for _, item in seleccionados.iterrows():
                    cant_pedir = int(item['Faltante_Min']) if item['Faltante_Min'] > 0 else 1
                    mensaje += f"- {item['Nombre']}: Faltan {cant_pedir}\n"
                
                st.text_area("Copia este mensaje para WhatsApp:", value=mensaje, height=200, key="txt_wsp_p1")

        st.divider()
        if st.button("🔄 RECALCULAR STOCK MÍNIMO/MÁXIMO", key="btn_recalc_p1"):
            ids_a_recalcular = df_f['ID_Producto'].astype(str).tolist() if 'ID_Producto' in df_f.columns else []
            cant_prods = len(ids_a_recalcular)
            with st.spinner(f"Calculando rotación de 60 días para {cant_prods} producto(s)..."):
                exito = stock_service.calcular_y_actualizar_stock_automatico(ids_filtrados=ids_a_recalcular)
                if exito:
                    st.success(f"¡Stock mínimo y máximo actualizado para {cant_prods} productos!")
                    st.rerun()
                else:
                    st.warning("No se encontraron registros de ventas suficientes para recalcular el stock.")

    # -----------------------------------------------------------------
    # PESTAÑA 2: PRIORIZACIÓN DE COMPRAS (ANÁLISIS ABC + URGENCIA)
    # -----------------------------------------------------------------
    with tab_priorizacion:
        st.subheader("🎯 Ranking de Priorización de Compras")
        st.caption("Clasifica productos según su relevancia comercial (ABC) y urgencia por faltante de stock mínimo.")
        
        busqueda_abc = st.text_input(
            "🔍 Buscar por nombre o código en el ranking:", 
            placeholder="Ej: pampers, babydry, 779...",
            key="busqueda_texto_abc"
        )

        fa1, fa2, fa3 = st.columns(3)
        p_rubro = fa1.selectbox("Rubro", rubros, key="p_rubro_abc")
        p_marca = fa2.selectbox("Marca", marcas, key="p_marca_abc")
        p_prov = fa3.selectbox("Proveedor", provs, key="p_prov_abc")
        
        dias_analisis = st.slider("Días de historia de ventas para scoring:", min_value=15, max_value=90, value=60, step=15, key="slider_dias_abc")

        # Cargar detalles de ventas
        df_vd = stock_service.obtener_ventas_detalle()
        df_ranking = df_prod.copy()
        
        if 'Estado' in df_ranking.columns:
            df_ranking = df_ranking[df_ranking['Estado'] != 'INACTIVO']

        if 'Es_Stockeable' in df_ranking.columns:
            df_ranking = df_ranking[df_ranking['Es_Stockeable'] == True]

        if 'Rubro' in df_ranking.columns and 'Nombre' in df_ranking.columns:
            es_leche = df_ranking['Rubro'].astype(str).str.upper() == 'LECHE'
            contiene_bulto = df_ranking['Nombre'].astype(str).str.contains(' x12| x24| x30| x400| x800| x1000| x1200', case=False, na=False)
            df_ranking = df_ranking[~es_leche | contiene_bulto]

        df_ranking['Stock_Actual'] = pd.to_numeric(df_ranking['Stock_Actual'], errors='coerce').fillna(0)
        df_ranking['Stock_Min'] = pd.to_numeric(df_ranking['Stock_Min'], errors='coerce').fillna(0)
        df_ranking['Stock_Max'] = pd.to_numeric(df_ranking['Stock_Max'], errors='coerce').fillna(0)

        if busqueda_abc:
            b_txt = busqueda_abc.lower()
            mask_abc = df_ranking['Nombre'].astype(str).str.lower().str.contains(b_txt, na=False) | \
                       df_ranking['ID_Producto'].astype(str).str.lower().str.contains(b_txt, na=False)
            df_ranking = df_ranking[mask_abc]

        if p_rubro != "Todos":
            df_ranking = df_ranking[df_ranking['Rubro'] == p_rubro]
        if p_marca != "Todos":
            df_ranking = df_ranking[df_ranking['Marca'] == p_marca]
        if p_prov != "Todos":
            if 'Proveedor' in df_ranking.columns:
                df_ranking = df_ranking[df_ranking['Proveedor'] == p_prov]
            elif 'ID_Proveedor' in df_ranking.columns and not df_prov.empty:
                prov_sel_abc = df_prov[df_prov['Razon_Social'] == p_prov]
                if not prov_sel_abc.empty:
                    id_p_abc = prov_sel_abc.iloc[0]['ID_Proveedor']
                    df_ranking = df_ranking[df_ranking['ID_Proveedor'] == id_p_abc]

        if df_ranking.empty:
            st.info("No se encontraron productos con los criterios, texto y filtros seleccionados.")
        else:
            if not df_vd.empty:
                df_vd['Cantidad'] = pd.to_numeric(df_vd['Cantidad'], errors='coerce').fillna(0)
                df_vd['Subtotal'] = pd.to_numeric(df_vd['Subtotal'], errors='coerce').fillna(0)
                df_vd['Precio_Costo_Unitario'] = pd.to_numeric(df_vd['Precio_Costo_Unitario'], errors='coerce').fillna(0)
                df_vd['Ganancia_Real'] = df_vd['Subtotal'] - (df_vd['Cantidad'] * df_vd['Precio_Costo_Unitario'])

                agrupado = df_vd.groupby('ID_Producto').agg({
                    'Cantidad': 'sum',
                    'Subtotal': 'sum',
                    'Ganancia_Real': 'sum'
                }).reset_index().rename(columns={
                    'Cantidad': 'Rotacion_Unid',
                    'Subtotal': 'Facturacion_Total',
                    'Ganancia_Real': 'Ganancia_Total'
                })
                
                df_ranking['ID_Producto'] = df_ranking['ID_Producto'].astype(str)
                agrupado['ID_Producto'] = agrupado['ID_Producto'].astype(str)
                
                df_ranking = pd.merge(df_ranking, agrupado, on='ID_Producto', how='left')
            else:
                df_ranking['Rotacion_Unid'] = 0
                df_ranking['Facturacion_Total'] = 0.0
                df_ranking['Ganancia_Total'] = 0.0

            df_ranking['Rotacion_Unid'] = df_ranking['Rotacion_Unid'].fillna(0)
            df_ranking['Facturacion_Total'] = df_ranking['Facturacion_Total'].fillna(0.0)
            df_ranking['Ganancia_Total'] = df_ranking['Ganancia_Total'].fillna(0.0)

            max_rot = df_ranking['Rotacion_Unid'].max()
            max_fact = df_ranking['Facturacion_Total'].max()
            max_gan = df_ranking['Ganancia_Total'].max()

            norm_rot = (df_ranking['Rotacion_Unid'] / max_rot * 100) if max_rot > 0 else 0
            norm_fact = (df_ranking['Facturacion_Total'] / max_fact * 100) if max_fact > 0 else 0
            norm_gan = (df_ranking['Ganancia_Total'] / max_gan * 100) if max_gan > 0 else 0

            df_ranking['Score_Comercial'] = (0.40 * norm_fact) + (0.35 * norm_rot) + (0.25 * norm_gan)

            def asignar_categoria(score, p70, p30):
                if score >= p70 and score > 0:
                    return "🟢 Categoría A"
                elif score >= p30 and score > 0:
                    return "🟡 Categoría B"
                else:
                    return "🔴 Categoría C"

            p70 = df_ranking['Score_Comercial'].quantile(0.70)
            p30 = df_ranking['Score_Comercial'].quantile(0.30)
            
            df_ranking['Categoria_ABC'] = df_ranking['Score_Comercial'].apply(lambda x: asignar_categoria(x, p70, p30))

            df_ranking['Faltante_Min'] = (df_ranking['Stock_Min'] - df_ranking['Stock_Actual']).clip(lower=0)
            
            def calc_urgencia(row):
                if row['Stock_Min'] > 0 and row['Faltante_Min'] > 0:
                    return (row['Faltante_Min'] / row['Stock_Min']) * 100
                return 0.0

            df_ranking['Urgencia_%'] = df_ranking.apply(calc_urgencia, axis=1)

            df_ranking['Orden_Cat'] = df_ranking['Categoria_ABC'].map({
                "🟢 Categoría A": 1,
                "🟡 Categoría B": 2,
                "🔴 Categoría C": 3
            })
            
            df_ranking = df_ranking.sort_values(
                by=['Orden_Cat', 'Urgencia_%', 'Score_Comercial'], 
                ascending=[True, False, False]
            ).reset_index(drop=True)

            df_ranking['Pedir'] = df_ranking['Urgencia_%'] > 0
            
            cols_abc_mostrar = ['Pedir', 'Categoria_ABC', 'Nombre', 'Urgencia_%', 'Stock_Actual', 'Stock_Min', 'Faltante_Min', 'Score_Comercial']
            cols_abc_presentes = [c for c in cols_abc_mostrar if c in df_ranking.columns]

            st.markdown("---")
            st.caption("📌 Los artículos con stock por debajo del mínimo vienen tildados automáticamente. Podés destildar o sumar los que desees.")

            df_abc_editado = st.data_editor(
                df_ranking[cols_abc_presentes],
                column_config={
                    "Pedir": st.column_config.CheckboxColumn("📱 Pedir", default=False),
                    "Categoria_ABC": st.column_config.TextColumn("Categoría"),
                    "Nombre": st.column_config.TextColumn("Producto"),
                    "Urgencia_%": st.column_config.NumberColumn("Urgencia (%)", format="%.0f%%"),
                    "Stock_Actual": st.column_config.NumberColumn("Stock Act."),
                    "Stock_Min": st.column_config.NumberColumn("Mínimo"),
                    "Faltante_Min": st.column_config.NumberColumn("Faltante a Mín."),
                    "Score_Comercial": st.column_config.NumberColumn("Score", format="%.1f pts")
                },
                disabled=['Categoria_ABC', 'Nombre', 'Urgencia_%', 'Stock_Actual', 'Stock_Min', 'Faltante_Min', 'Score_Comercial'],
                hide_index=True,
                use_container_width=True,
                key="editor_tabla_abc"
            )

            col_abc_wsp, col_abc_exp = st.columns(2)
            
            if col_abc_wsp.button("💬 Generar WhatsApp Priorizado", type="primary", key="btn_wsp_abc"):
                sel_abc = df_abc_editado[df_abc_editado['Pedir'] == True]
                
                if sel_abc.empty:
                    st.warning("⚠️ No seleccionaste ningún producto. Tildá las casillas en la columna '📱 Pedir'.")
                else:
                    msg_abc = ""
                    for _, r in sel_abc.iterrows():
                        cant_comprar = int(r['Faltante_Min']) if r['Faltante_Min'] > 0 else 1
                        rubro_prod = str(r.get('Rubro', '')).strip().upper()
                        
                        if rubro_prod == "LECHE":
                            unid_texto = "fardo" if cant_comprar == 1 else "fardos"
                        else:
                            unid_texto = "unidad" if cant_comprar == 1 else "unidades"
                        
                        msg_abc += f"{cant_comprar} {unid_texto} *{r['Nombre']}*\n"
                    
                    st.text_area("Copiar mensaje para proveedor:", value=msg_abc, height=220, key="txt_area_abc")

            df_export_excel = df_ranking[df_ranking['Urgencia_%'] > 0].drop(columns=['Pedir', 'Orden_Cat'], errors='ignore')

            if not df_export_excel.empty:
                buffer_abc = io.BytesIO()
                with pd.ExcelWriter(buffer_abc, engine='xlsxwriter') as writer_abc:
                    df_export_excel.to_excel(writer_abc, index=False)
                
                col_abc_exp.download_button(
                    label=f"📥 Exportar Recomendados ({len(df_export_excel)}) a Excel",
                    data=buffer_abc.getvalue(),
                    file_name="productos_recomendados_compra.xlsx",
                    mime="application/vnd.ms-excel",
                    key="btn_exp_excel_abc"
                )
            else:
                col_abc_exp.info("🟢 No hay productos con urgencia mayor al 0% para exportar.")

# Aliases de compatibilidad requeridos por ejecutar_vista
mostrar_vista_stock = render
render_stock_view = render
main = render
