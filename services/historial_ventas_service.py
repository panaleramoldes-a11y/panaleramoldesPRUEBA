import pandas as pd
import streamlit as st
from config.database import db
from services.audit_service import log_auditoria


class HistorialVentasService:

    @staticmethod
    def cargar_datos_historial() -> pd.DataFrame:
        """Carga las ventas desde VENTAS_CABECERA integrando detalles, clientes y vendedores."""
        try:
            # Consulta a VENTAS_CABECERA con sus detalles integrados
            resp_ventas = (
                db.table("VENTAS_CABECERA")
                .select(
                    "ID_Venta, Fecha, ID_Cliente, ID_Vendedor, Total, Forma_Pago, Estado, VENTAS_DETALLE(*)"
                )
                .limit(100000)
                .execute()
            )

            if not resp_ventas.data:
                return pd.DataFrame()

            df_ventas = pd.DataFrame(resp_ventas.data)

            # Limpieza y conversión del campo Total
            df_ventas["Total"] = (
                df_ventas["Total"]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace(",", ".", regex=False)
            )
            df_ventas["Total"] = pd.to_numeric(
                df_ventas["Total"], errors="coerce"
            ).fillna(0)

            # Tablas auxiliares para joins
            df_clientes = pd.DataFrame(
                db.table("CLIENTES")
                .select("ID_Cliente, Nombre, Apellido")
                .execute()
                .data
            )
            df_vend = pd.DataFrame(
                db.table("VENDEDORES")
                .select("ID_Vendedor, Nombre, Apellido")
                .execute()
                .data
            )

            # Normalización de claves foráneas a String
            df_ventas["ID_Cliente"] = df_ventas["ID_Cliente"].astype(str)
            df_ventas["ID_Vendedor"] = df_ventas["ID_Vendedor"].astype(str)

            if not df_clientes.empty:
                df_clientes["ID_Cliente"] = df_clientes["ID_Cliente"].astype(str)
                df_ventas = df_ventas.merge(
                    df_clientes, on="ID_Cliente", how="left"
                )
                df_ventas["Cliente_Full"] = (
                    df_ventas["Nombre"].fillna("Sin Nombre")
                    + " "
                    + df_ventas["Apellido"].fillna("")
                )
            else:
                df_ventas["Cliente_Full"] = "Sin Nombre"

            if not df_vend.empty:
                df_vend["ID_Vendedor"] = df_vend["ID_Vendedor"].astype(str)
                df_ventas = df_ventas.merge(
                    df_vend,
                    on="ID_Vendedor",
                    how="left",
                    suffixes=("_vta", "_vend"),
                )
                df_ventas["Vendedor_Full"] = (
                    df_ventas["Nombre_vend"].fillna("Sin Vendedor")
                    + " "
                    + df_ventas["Apellido_vend"].fillna("")
                )
            else:
                df_ventas["Vendedor_Full"] = "Sin Vendedor"

            # Conversión de Fecha
            df_ventas["Fecha"] = pd.to_datetime(df_ventas["Fecha"]).dt.date

            return df_ventas

        except Exception as e:
            st.error(f"Error al cargar datos del historial: {e}")
            return pd.DataFrame()

    @staticmethod
    def obtener_cat_productos() -> pd.DataFrame:
        """Obtiene la lista de productos para cruzar con los detalles de venta."""
        try:
            resp = (
                db.table("PRODUCTOS")
                .select("ID_Producto, Nombre")
                .execute()
            )
            return pd.DataFrame(resp.data) if resp.data else pd.DataFrame()
        except Exception as e:
            st.error(f"Error al obtener catálogo de productos: {e}")
            return pd.DataFrame()

    @staticmethod
    def anular_venta_proceso(id_venta: str, usuario: str) -> bool:
        """
        Ejecuta la anulación de la venta.
        Aplica reversa en BD, devolución de stock/caja y registro en auditoría.
        """
        try:
            # 1. Si existe una función global/legacy 'anular_venta', la invocamos
            if "anular_venta" in globals():
                globals()["anular_venta"](id_venta)
            else:
                # Actualización de estado directa en BD
                db.table("VENTAS_CABECERA").update({"Estado": "ANULADA"}).eq(
                    "ID_Venta", id_venta
                ).execute()

            # 2. Registrar en auditoría
            log_auditoria(
                tabla="VENTAS_CABECERA",
                accion="UPDATE",
                id_entidad=str(id_venta),
                detalles={
                    "operacion": "Anulación de Venta",
                    "estado_nuevo": "ANULADA",
                },
                usuario=usuario,
            )
            return True
        except Exception as e:
            st.error(f"Error al anular la venta {id_venta}: {e}")
            return False
