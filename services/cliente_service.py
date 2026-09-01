import pandas as pd
from config.database import db
from services.audit_service import log_auditoria

def obtener_clientes():
    try:
        response = db.table("CLIENTES").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        raise Exception(f"Error al conectar con Supabase: {e}")

def crear_cliente(datos_cliente, usuario_logueado):
    resultado = db.table("CLIENTES").insert(datos_cliente).execute()
    
    id_cliente_generado = "N/A"
    if resultado.data:
        id_cliente_generado = resultado.data[0].get('ID_Cliente', resultado.data[0].get('id', 'N/A'))

    # Log de Auditoría
    log_auditoria(
        tabla="CLIENTES",
        accion="INSERT",
        id_entidad=id_cliente_generado,
        detalles={
            "operacion": "Alta de Cliente",
            "datos_cliente": {
                "nombre_completo": f"{datos_cliente.get('Apellido')}, {datos_cliente.get('Nombre')}",
                "razon_social": datos_cliente.get('Razón Social', 'N/A'),
                "telefono": datos_cliente.get('Telefono'),
                "dni_cuit": datos_cliente.get('CUIT') if datos_cliente.get('CUIT') else datos_cliente.get('DNI'),
                "zona": datos_cliente.get('Zona'),
                "tipo_cliente": datos_cliente.get('Tipo_Cliente'),
                "direccion_principal": datos_cliente.get('Direccion_1')
            }
        },
        usuario=usuario_logueado
    )
    return resultado

def actualizar_cliente(id_cliente, datos_actualizados, datos_previos, usuario_logueado):
    db.table("CLIENTES").update(datos_actualizados).eq("ID_Cliente", int(id_cliente)).execute()

    razon_antigua = datos_previos.get('Razón Social', '')
    nombre_antiguo = razon_antigua if razon_antigua else f"{datos_previos.get('Apellido', '')}, {datos_previos.get('Nombre', '')}"
    
    razon_nueva = datos_actualizados.get('Razón Social', '')
    nombre_nuevo = razon_nueva if razon_nueva else f"{datos_actualizados.get('Apellido', '')}, {datos_actualizados.get('Nombre', '')}"

    log_auditoria(
        tabla="CLIENTES",
        accion="UPDATE",
        id_entidad=id_cliente,
        detalles={
            "operacion": "Modificar Cliente",
            "antes": {
                "nombre_comercial_o_completo": nombre_antiguo,
                "telefono": datos_previos.get('Telefono'),
                "zona": datos_previos.get('Zona'),
                "direccion_1": datos_previos.get('Direccion_1')
            },
            "despues": {
                "nombre_comercial_o_completo": nombre_nuevo,
                "telefono": datos_actualizados.get('Telefono'),
                "zona": datos_actualizados.get('Zona'),
                "direccion_1": datos_actualizados.get('Direccion_1')
            }
        },
        usuario=usuario_logueado
    )

def eliminar_cliente(id_cliente, datos_previos, usuario_logueado):
    db.table("CLIENTES").delete().eq("ID_Cliente", int(id_cliente)).execute()

    razon_antigua = datos_previos.get('Razón Social', '')
    cliente_identificador = razon_antigua if razon_antigua else f"{datos_previos.get('Apellido', '')}, {datos_previos.get('Nombre', '')}"

    log_auditoria(
        tabla="CLIENTES",
        accion="DELETE",
        id_entidad=id_cliente,
        detalles={
            "operacion": "Eliminar Cliente",
            "cliente_eliminado": cliente_identificador,
            "dni_cuit": datos_previos.get('CUIT') if datos_previos.get('CUIT') else datos_previos.get('DNI'),
            "telefono": datos_previos.get('Telefono')
        },
        usuario=usuario_logueado
    )

def obtener_gift_card_activa(id_cliente):
    return db.table("GIFT_CARDS").select("*").eq("ID_Cliente", int(id_cliente)).eq("Estado", True).execute().data
