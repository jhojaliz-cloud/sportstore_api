from fastapi import FastAPI
import xmlrpc.client

app = FastAPI()

# 🔐 CONFIG ODOO
url = 'https://icaltex.odoo.com'
db = 'icaltex'
username = 'jhojaliz@gmail.com'
password = 'ad396eee636586ff637659eeab39122ab7d1bf62'


# 🔌 CONEXIÓN DINÁMICA ODOO
def conectar_odoo():

    common = xmlrpc.client.ServerProxy(
        f'{url}/xmlrpc/2/common',
        allow_none=True
    )

    uid = common.authenticate(
        db,
        username,
        password,
        {}
    )

    models = xmlrpc.client.ServerProxy(
        f'{url}/xmlrpc/2/object',
        allow_none=True
    )

    return uid, models


# 🧠 LIMPIADOR
def limpiar(texto):
    return str(texto).replace("-", "").replace(" ", "").strip().lower()


# 🎨 COLORES SOPORTADOS
COLORES = [
    "blanco",
    "negro",
    "rojo",
    "azul",
    "verde",
    "gris",
    "beige"
]


# 🔍 OBTENER PRODUCTOS
def obtener_productos():

    uid, models = conectar_odoo()

    productos = models.execute_kw(
        db,
        uid,
        password,
        'product.product',
        'search_read',
        [[['qty_available', '>', 0]]],
        {
            'fields': [
                'id',
                'name',
                'qty_available',
                'list_price',
                'product_template_attribute_value_ids'
            ],
            'limit': 500
        }
    )

    resultado = []

    for p in productos:

        atributos = []

        try:

            if p.get('product_template_attribute_value_ids'):

                valores = models.execute_kw(
                    db,
                    uid,
                    password,
                    'product.template.attribute.value',
                    'read',
                    [p['product_template_attribute_value_ids']],
                    {'fields': ['name']}
                )

                atributos = [
                    limpiar(v['name'])
                    for v in valores
                ]

        except:
            atributos = []

        p['atributos'] = atributos

        resultado.append(p)

    return resultado


# 🧠 EXTRAER DATOS
def extraer_datos(texto):

    texto_original = texto.lower()

    talla = ""
    color = ""

    # 🔥 detectar talla
    for palabra in texto_original.split():

        palabra_limpia = palabra.replace(",", "").replace(".", "")

        if palabra_limpia.isdigit():
            talla = palabra_limpia

    # 🔥 detectar color
    for c in COLORES:

        if c in texto_original:
            color = c

    # 🔥 limpiar modelo
    modelo = texto_original

    # quitar colores
    for c in COLORES:
        modelo = modelo.replace(c, "")

    # quitar palabras basura
    basura = [
        "talla",
        "quiero",
        "deseo",
        "necesito",
        "unos",
        "unas",
        "tenis",
        "zapatos"
    ]

    for b in basura:
        modelo = modelo.replace(b, "")

    # quitar talla
    if talla:
        modelo = modelo.replace(talla, "")

    modelo = limpiar(modelo.strip())

    return modelo, talla, color


# 🔎 BUSCAR PRODUCTO
def buscar_producto(texto):

    try:

        modelo, talla, color = extraer_datos(texto)

        productos = obtener_productos()

        sugerencias = []

        for p in productos:

            nombre = limpiar(p.get("name", ""))

            atributos = p.get("atributos", [])

            talla_real = ""
            color_real = ""

            # 🔥 recorrer atributos
            for a in atributos:

                a_limpio = limpiar(a)

                # detectar talla
                for numero in range(20, 50):

                    if str(numero) in a_limpio:
                        talla_real = str(numero)

                # detectar color
                for c in COLORES:

                    if c in a_limpio:
                        color_real = c

            texto_producto = limpiar(nombre + " " + " ".join(atributos))

            # ✅ MATCH EXACTO
            if (
                modelo in texto_producto
                and talla == talla_real
                and (color == color_real if color else True)
                and p.get("qty_available", 0) > 0
            ):

                return {
                    "disponible": True,
                    "producto_id": p["id"],
                    "nombre": p["name"],
                    "talla": talla_real,
                    "color": color_real,
                    "stock": p["qty_available"],
                    "precio": p["list_price"],
                    "imagen": f"{url}/web/image/product.product/{p['id']}/image_1920",
                    "mensaje": f"Sí 😊 tengo disponible el {p['name']} color {color_real} talla {talla_real} por ${int(p['list_price']):,}. Tenemos {int(p['qty_available'])} unidades disponibles 👟"
                }

            # 🔥 sugerencias
            if (
                modelo in texto_producto
                and p.get("qty_available", 0) > 0
            ):

                sugerencias.append({
                    "producto_id": p["id"],
                    "nombre": p["name"],
                    "talla": talla_real,
                    "color": color_real,
                    "stock": p["qty_available"],
                    "precio": p["list_price"]
                })

        # 🔥 sugerencias encontradas
        if sugerencias:

            return {
                "disponible": False,
                "mensaje": "No encontré exactamente esa combinación, pero tengo estas opciones disponibles 😊",
                "sugerencias": sugerencias[:5]
            }

        # ❌ sin resultados
        return {
            "disponible": False,
            "mensaje": "Producto agotado por ahora 😔"
        }

    except Exception as e:

        return {
            "disponible": False,
            "mensaje": f"Error interno: {str(e)}"
        }


# 📦 ENDPOINT PRODUCTO
@app.get("/producto")
def get_producto(texto: str = ""):

    # ✅ verificación webhook
    if texto == "":

        return {
            "status": "ok"
        }

    return {
    "data": buscar_producto(texto)
}


# 🛒 CREAR PEDIDO
@app.get("/crear-pedido")
def crear_pedido(
    nombre: str,
    telefono: str,
    ciudad: str,
    direccion: str,
    producto_id: int
):

    try:

        uid, models = conectar_odoo()

        # 🔎 buscar cliente
        partners = models.execute_kw(
            db,
            uid,
            password,
            'res.partner',
            'search_read',
            [[['phone', '=', telefono]]],
            {
                'fields': ['id'],
                'limit': 1
            }
        )

        # 👤 crear cliente
        if partners:

            partner_id = partners[0]['id']

        else:

            partner_id = models.execute_kw(
                db,
                uid,
                password,
                'res.partner',
                'create',
                [{
                    'name': nombre,
                    'phone': telefono,
                    'city': ciudad,
                    'street': direccion
                }]
            )

        # 🛒 crear pedido
        order_id = models.execute_kw(
            db,
            uid,
            password,
            'sale.order',
            'create',
            [{
                'partner_id': partner_id
            }]
        )

        # 📦 agregar producto
        models.execute_kw(
            db,
            uid,
            password,
            'sale.order.line',
            'create',
            [{
                'order_id': order_id,
                'product_id': producto_id,
                'product_uom_qty': 1
            }]
        )

        return {
            "success": True,
            "mensaje": "Pedido creado correctamente 😊",
            "order_id": order_id,
            "cliente_id": partner_id,
            "mensaje_whatsapp": f"👟 Pedido confirmado\n📦 Pedido #{order_id}\n🚚 Te contactaremos para coordinar el envío"
        }

    except Exception as e:

        return {
            "success": False,
            "mensaje": str(e)
        }


# 🧪 DEBUG PRODUCTOS
@app.get("/debug-productos")
def debug_productos():

    productos = obtener_productos()

    return productos[:20]   