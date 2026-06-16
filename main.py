from fastapi import FastAPI
import xmlrpc.client
from rapidfuzz import fuzz
from pydantic import BaseModel
from typing import List

app = FastAPI()
class Par(BaseModel):
    color: str
    talla: str


class PedidoLanding(BaseModel):
    nombre: str
    telefono: str
    ciudad: str
    direccion: str
    barrio: str

    producto: str
    combo: str
    total: float

    pares: List[Par]

    origen: str = "TikTok"

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

    "blanco","negro","gris","grisclaro","grisoscuro","plata","plateado",

    "rojo","rojooscuro","rojoborgona","vinotinto","granate","carmesi",

    "azul","azulclaro","azuloscuro","azulmarino","azulrey",
    "azulpetroleo","azulceleste","azulturquesa",

    "verde","verdeoscuro","verdeclaro","verdemilitar",
    "verdeoliva","verdeesmeralda","verdelimon",

    "amarillo","amarilloclaro","mostaza","dorado","oro",

    "naranja","coral","salmon","durazno",

    "rosado","rosa","fucsia","magenta","palo de rosa",

    "morado","violeta","lila","lavanda","purpura",

    "cafe","café","marron","marrón","chocolate","choco",
    "miel","caramelo","camel","caoba","tabaco","avellana",
    "capuccino","cappuccino","latte","arena","tierra",

    "beige","crema","marfil","hueso","perla",

    "khaki","caqui","taupe","topo",

    "cobre","bronce",

    "multicolor","estampado","animalprint","camuflado",

    "aguamarina","menta","mint","jade",

    "terracota","terracotta",

    "champaña","champagne",

    "grafito","antracita",

    "denim","jean","indigo","índigo",

    "cherry","cereza",

    "wine","burgundy","bordo","bordeaux",

    "ivory","offwhite","off-white",

    "petroleo","petróleo",

    "turquesa","aqua","aquamarina",

    "verdebotella","verdebosque","verdepino",

    "azulhielo","azulacero","azulcobalto",

    "rosa viejo","rosaviejo",

    "piel","nude",

    "taba","tan",

    "ceniza",

    "perlado",

    "metalizado",

    "neon","neón",

    "amarilloneon","verdeneon","naranjaneon","rosaneon",

    "blancoroto",

    "grisperla",

    "griscemento",

    "grisplomo",

    "grisgrafito",

    "azulink",

    "azulnavy",

    "navy",

    "chocolateoscuro",

    "chocolateclaro",

    "cafetostado",

    "cafemoka",

    "moka",

    "mocca",

    "espresso",

    "cognac",

    "whisky",

    "almendra",

    "almond",

    "sand",

    "sandia",

    "mentaoscuro",

    "oliva",

    "olive",

    "forest",

    "forestgreen",

    "military",

    "militar",

    "ice",

    "iceblue",

    "skyblue",

    "royalblue",

    "electricblue",

    "electric",

    "lime",

    "limegreen",

    "negro mate",

    "negromate",

    "negrobrillante",

    "charol",

    "charolnegro",

    "charolbeige",

    "charolmiel",

    "charolchocolate",

    "suela",

    "gum",

    "gumsole"
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
        print("TEXTO ORIGINAL:", texto)
        print("MODELO:", modelo)
        print("TALLA:", talla)
        print("COLOR:", color)

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
                if a_limpio.isdigit():
                    talla_real = a_limpio
                
                # todo lo que no sea talla se toma como atributo/color
                else:
                    
                    color_real = a_limpio

            texto_producto = limpiar(nombre + " " + " ".join(atributos))

            # ✅ MATCH INTELIGENTE
            score = fuzz.partial_ratio(
                modelo.lower(),
                texto_producto.lower()
            )
            print("MODELO:", modelo)
            print("PRODUCTO:", texto_producto)
            print("SCORE:", score)

            if (
                score >= 70
                and (talla == talla_real if talla else True)
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

            # 🔥 sugerencias inteligentes
            score_sugerencia = fuzz.partial_ratio(
                modelo.lower(),
                texto_producto.lower()
            )

            if (
                score_sugerencia >= 60
                and p.get("qty_available", 0) > 0
            ):
                
                # detectar color dinámicamente desde el texto
                if color_real and color_real in limpiar(texto):
                    color = color_real

                sugerencias.append({
                    "producto_id": p["id"],
                    "nombre": p["name"],
                    "talla": talla_real,
                    "color": color_real,
                    "stock": p["qty_available"],
                    "precio": p["list_price"]
                })
                print("TOTAL SUGERENCIAS:", len(sugerencias))
                print("TALLA BUSCADA:", talla)
                print("COLOR BUSCADO:", color)
                
                # CONSULTA DE CATALOGO
        if sugerencias and not talla and not color:

            primera = sugerencias[0]

            tallas = sorted(
                list(
                    set(
                        [s["talla"] for s in sugerencias if s["talla"]]
                    )
                )
            )
            colores = sorted(
                list(
                    set(
                        [s["color"] for s in sugerencias if s["color"]]
                    )
                )
            )

            return {
                "disponible": True,
                "producto_id": primera["producto_id"],
                "nombre": primera["nombre"],
                "colores": colores,
                "precio": primera["precio"],
                "imagen": f"{url}/web/image/product.product/{primera['producto_id']}/image_1920",
                "mensaje": f"Sí 😊 tengo disponible el {primera['nombre']} en los colores {', '.join(colores)}. Lo manejamos en tallas {', '.join(tallas)} por ${int(primera['precio']):,} 👟"
            }

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

    return {
        "total_productos": len(productos)
    }

# 🧠 CREAR LEAD
def crear_lead(datos):

    uid, models = conectar_odoo()

    descripcion = f"""
Producto: {datos.producto}
Combo: {datos.combo}
Total: ${datos.total}

Pares:
"""

    for i, par in enumerate(datos.pares, start=1):

        descripcion += f"""
Par {i}
Color: {par.color}
Talla: {par.talla}
"""

    descripcion += f"""

Dirección: {datos.direccion}
Barrio: {datos.barrio}
Origen: {datos.origen}
"""

    lead_id = models.execute_kw(
        db,
        uid,
        password,
        'crm.lead',
        'create',
        [{
            'name': f'TL-{datos.nombre}',
            'contact_name': datos.nombre,
            'phone': datos.telefono,
            'city': datos.ciudad,
            'street': datos.direccion,
            'description': descripcion,
            'source_id': False
        }]
    )

    return lead_id


@app.post("/api/landing/order")
def landing_order(datos: PedidoLanding):

    try:

        lead_id = crear_lead(datos)

        return {
            "success": True,
            "lead_id": lead_id,
            "codigo": f"TL-{lead_id}",
            "mensaje": "Lead creado correctamente"
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }