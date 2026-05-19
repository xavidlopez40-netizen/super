import streamlit as st
import sqlite3
import qrcode
from io import BytesIO

# ================= CONFIGURACIÓN DE LA PÁGINA WEB =================
st.set_page_config(page_title="SUPERMERCADO JAX", layout="wide")

# ================= CONEXIÓN Y CREACIÓN DE BASE DE DATOS =================
# Usamos 'check_same_thread=False' porque en entorno Web múltiples usuarios pueden conectar
conn = sqlite3.connect("supermercado.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pasillo TEXT,
    producto TEXT,
    precio REAL,
    piezas INTEGER
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT,
    saldo REAL
)""")
conn.commit()

# Insertar datos iniciales si la base de datos web está vacía
cursor.execute("SELECT COUNT(*) FROM productos")
if cursor.fetchone()[0] == 0:
    datos_iniciales = [
        ("Limpieza", "Detergente", 5.50, 20), ("Limpieza", "Cloro", 2.10, 15), ("Limpieza", "Jabon", 1.80, 25),
        ("Panaderia", "Bolillo", 0.50, 50), ("Panaderia", "Pastel", 18.00, 3), ("Panaderia", "Donas", 1.20, 12),
        ("Lacteos", "Leche", 1.20, 30), ("Lacteos", "Queso", 4.50, 12), ("Lacteos", "Yogurt", 0.80, 40),
        ("Carniceria", "Pollo", 5.00, 10), ("Carniceria", "Res", 12.00, 8), ("Carniceria", "Cerdo", 9.00, 10),
        ("Frutas", "Manzana", 0.60, 40), ("Frutas", "Platano", 0.30, 50), ("Frutas", "Uvas", 4.00, 15)
    ]
    cursor.executemany("INSERT INTO productos (pasillo, producto, precio, piezas) VALUES (?, ?, ?, ?)", datos_iniciales)
    conn.commit()

cursor.execute("SELECT COUNT(*) FROM clientes")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO clientes (numero, saldo) VALUES (?, ?)", ("XXXX-9999", 750.0))
    conn.commit()

# ================= VARIABLES DE SESIÓN (ESTADO DE LA APLICACIÓN) =================
if "carrito" not in st.session_state:
    st.session_state.carrito = {}
if "total" not in st.session_state:
    st.session_state.total = 0.0
if "pasillo_actual" not in st.session_state:
    st.session_state.pasillo_actual = "Limpieza"

# Extraer saldo actual de la base de datos
cursor.execute("SELECT saldo FROM clientes LIMIT 1")
saldo_disponible = cursor.fetchone()[0]

# ================= BARRA SUPERIOR E INTERFAZ ORIGINAL =================
st.title("🛒 SUPERMERCADO JAX")
st.subheader(f"💳 Saldo disponible: ${saldo_disponible:.2f}")

# ----- SECCIÓN DEL CÓDIGO QR COMPARTIBLE -----
# Expansor discreto para mostrar u ocultar el QR en la app web
with st.expander("📱 Compartir App (Código QR)"):
    # REEMPLAZA ESTO con la URL final cuando subas tu App a internet (ej. share.streamlit.io)
    url_publica ="https://b6k4rgkhnxsxxcxwfahhvu.streamlit.app/"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url_publica)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    
    # Procesar la imagen en memoria para mostrarla en la web sin guardarla en disco
    buf = BytesIO()
    img_qr.save(buf, format="PNG")
    byte_im = buf.getvalue()
    
    st.image(byte_im, caption="¡Escanea este QR desde cualquier celular para abrir la tienda directamente!", width=230)

st.write("---")

# Distribución en 3 columnas simulando los 3 "Frames" de Tkinter
col1, col2, col3 = st.columns([1.5, 2.5, 2])

# ================= COLUMNA 1: PASILLOS =================
with col1:
    st.markdown("### 🏬 PASILLOS")
    cursor.execute("SELECT DISTINCT pasillo FROM productos")
    lista_pasillos = [fila[0] for fila in cursor.fetchall()]
    
    for pasillo in lista_pasillos:
        # Si presionas el botón del pasillo, cambia el estado actual
        if st.button(pasillo, use_container_width=True):
            st.session_state.pasillo_actual = pasillo

# ================= COLUMNA 2: PRODUCTOS =================
with col2:
    st.markdown(f"### 📦 PRODUCTOS: {st.session_state.pasillo_actual.upper()}")
    
    cursor.execute("SELECT producto, precio, piezas FROM productos WHERE pasillo = ?", (st.session_state.pasillo_actual,))
    productos_db = cursor.fetchall()
    
    # Lista desplegable de selección
    opciones = [f"{p[0]} | ${p[1]:.2f} | Quedan {p[2]} piezas" for p in productos_db]
    seleccion = st.selectbox("Seleccione un producto:", opciones)
    
    if seleccion:
        producto_nombre = seleccion.split(" |")[0]
        # Obtener los detalles del producto seleccionado
        for p in productos_db:
            if p[0] == producto_nombre:
                precio_u = p[1]
                piezas_u = p[2]
        
        # Entrada de cantidad dinámica
        cantidad = st.number_input("¿Cuántas piezas?", min_value=1, max_value=max(1, piezas_u), value=1, step=1)
        
        if st.button("Agregar al carrito", type="primary"):
            subtotal = precio_u * cantidad
            
            if cantidad > piezas_u:
                st.error(f"Solo quedan {piezas_u} piezas.")
            elif st.session_state.total + subtotal > saldo_disponible:
                st.error("Saldo insuficiente en la tarjeta.")
            else:
                # Descontar temporalmente de SQLite
                cursor.execute("UPDATE productos SET piezas = ? WHERE producto = ?", (piezas_u - cantidad, producto_nombre))
                conn.commit()
                
                # Modificar carrito en memoria
                if producto_nombre in st.session_state.carrito:
                    st.session_state.carrito[producto_nombre]['cantidad'] += cantidad
                else:
                    st.session_state.carrito[producto_nombre] = {
                        'cantidad': cantidad, 
                        'precio': precio_u, 
                        'pasillo': st.session_state.pasillo_actual
                    }
                
                st.session_state.total += subtotal
                st.success(f"{producto_nombre} agregado correctamente.")
                st.rerun()

# ================= COLUMNA 3: CARRITO =================
with col3:
    st.markdown("### 🛍️ CARRITO")
    
    if not st.session_state.carrito:
        st.caption("El carrito está vacío.")
    else:
        for prod, info in list(st.session_state.carrito.items()):
            subtotal_item = info['cantidad'] * info['precio']
            st.write(f"**{prod}** | {info['cantidad']} pzs | ${subtotal_item:.2f}")
            
            # Botón integrado para regresar piezas (Devolver producto)
            if st.button(f"Devolver {prod}", key=f"btn_dev_{prod}"):
                cursor.execute("SELECT piezas FROM productos WHERE producto = ?", (prod,))
                piezas_v = cursor.fetchone()[0]
                cursor.execute("UPDATE productos SET piezas = ? WHERE producto = ?", (piezas_v + info['cantidad'], prod))
                conn.commit()
                
                st.session_state.total -= subtotal_item
                del st.session_state.carrito[prod]
                st.rerun()
                
    st.write("---")
    st.markdown(f"### **TOTAL: ${st.session_state.total:.2f}**")
    
    # Botón de pagar definitivo
    if st.button("PAGAR", use_container_width=True, type="secondary"):
        if st.session_state.total <= 0:
            st.warning("No hay productos en el carrito.")
        else:
            nuevo_saldo = saldo_disponible - st.session_state.total
            cursor.execute("UPDATE clientes SET saldo = ?", (nuevo_saldo,))
            conn.commit()
            
            st.balloons() # Efecto visual de celebración en la página web
            st.success(f"¡Pago realizado con éxito! Saldo restante: ${nuevo_saldo:.2f}")
            
            # Limpieza automática del carrito para continuar comprando en la ventana activa
            st.session_state.carrito.clear()
            st.session_state.total = 0.0
            st.rerun()
            
