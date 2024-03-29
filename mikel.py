# THIS PROJECT WAS DEVELOPED TO TAKE INVENTORY OF PRODUCTS USING QR CODES
__author__ = "John Acha"
__email__ = "john_acha@live.com"
__copyright__ = "Copyright © 2023"
__credits__ = "Liceli Ramos, Ken Acha, Lynn Acha"
__license__ = "GPLv3"
__version__ = "1.1"
__message__ = "Make with love"

from PySide6 import QtWidgets, QtGui, QtCore, QtNetwork
from PySide6.QtCore import Qt, QUrl, QSize
from PySide6.QtGui import QAction, QFont, QCursor, QImage, QPixmap, QStandardItemModel, QStandardItem, QIcon, QDesktopServices 
from PySide6.QtWidgets import (
    QApplication,
    QStackedWidget,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QFileDialog,
    QScrollArea,
    QTreeView,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QCheckBox,
    QPushButton,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSizePolicy,
    QDialog
    
)
import sys, os
import csv
#import qrcode
#from PIL import Image
from io import BytesIO
import webbrowser
import sqlite3
#import numpy
#import openpyxl
#from openpyxl import Workbook
#from openpyxl.utils.dataframe import dataframe_to_rows
import logging
from datetime import datetime


basedir = os.path.dirname(__file__)

try:
    from ctypes import windll # Solo existe en Windows
    myappid = "mycompany.myproduct.subproduct.version"
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass    


# LOGO
LOGO_HOME = os.path.join(basedir, "image", "logo.webp")
#LOGO_HOME = os.path.join(basedir, "logo_color.png")

#from PIL import Image

def resize_image(input_image_path, output_image_path, size):
    original_image = Image.open(input_image_path)
    width, height = original_image.size
    print(f'Original image size: {width}x{height}')

    resized_image = original_image.resize(size)
    width, height = resized_image.size
    print(f'Resized image size: {width}x{height}')

    resized_image.show()
    resized_image.save(output_image_path)

# Uso de la función
#resize_image('logo_color.png', 'logo_color_resized.png', (500, 500))


# SOCIAL NETWORK
ICON_FACEBOOK = os.path.join(basedir, "icons", "facebook.svg")
ICON_GITHUB = os.path.join(basedir, "icons", "github.svg")
ICON_LINKEDIN = os.path.join(basedir, "icons", "linkedin.svg")
ICON_YOUTUBE = os.path.join(basedir, "icons", "youtube.svg")

# DOCUMENTATION
DOCUMENTATION = os.path.join(basedir, "document", "documentation.pdf")

# DATABASE NAME
DATABASE_NAME = os.path.join(basedir, "database.db")

# Configura el registro de eventos
logging.basicConfig(filename='event_log.log', level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

# Fecha de vencimiento fija (formato: año, mes, día)
expiration_date = datetime(2024, 11, 14)

#--------------------------------------------------# DATABASE MANAGER #--------------------------------------------------#
class DatabaseManager:

    def __init__(self, database_name):
        self.database_name = database_name
        self.connection = None
        self.cursor = None
        self.connect_database()

    def connect_database(self):
        try:
            self.connection = sqlite3.connect(self.database_name)
            self.cursor = self.connection.cursor()
            #print("Conexión a la base de datos exitosa.")
            self.create_product_table()
            self.create_inventory_table()
        except sqlite3.Error as e:
            raise Exception("Error al conectar con la base de datos.") from e

    def create_product_table(self):
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT(10) NOT NULL,
                    name TEXT(100) NOT NULL,
                    lot TEXT(20) NOT NULL,
                    location TEXT(20) NOT NULL,
                    quantity INTEGER NOT NULL
                )
            ''')
            self.connection.commit()
        except sqlite3.Error as e:
            raise Exception("Error al crear la tabla de productos.") from e

    def create_inventory_table(self):
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    code TEXT(10) NOT NULL,
                    name TEXT(100) NOT NULL,
                    lot TEXT(20) NOT NULL,
                    location TEXT(20) NOT NULL,
                    quantity INTEGER NOT NULL,
                    inventory INTEGER NOT NULL DEFAULT 0,  -- Nueva columna de existencias
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')
            self.connection.commit()
        except sqlite3.Error as e:
            raise Exception("Error al crear la tabla de inventario.") from e


    def perform_inventory(self, product_id, code, name, lot, location, quantity):
        try:
            # Verificar si ya existe una entrada para este producto en la tabla de inventario
            existing_entry = self.cursor.execute(
                "SELECT * FROM inventory WHERE product_id=?", (product_id,)
            ).fetchone()

            if existing_entry:
                # Si existe una entrada, actualiza la cantidad y las existencias
                new_quantity = existing_entry[5] + quantity
                new_inventory = existing_entry[7] + 1  # Aumenta las existencias
                self.cursor.execute(
                    "UPDATE inventory SET location=?, quantity=?, inventory=? WHERE product_id=?",
                    (location, new_quantity, new_inventory, product_id),
                )
            else:
                # Si no existe una entrada, crea una nueva
                self.cursor.execute(
                    "INSERT INTO inventory (product_id, code, name, lot, location, quantity, inventory) VALUES (?, ?, ?, ?, ?, ?, 1)",
                    (product_id, code, name, lot, location, quantity),
                )

            self.connection.commit()
        except sqlite3.Error as e:
            raise Exception("Error al realizar el inventario.") from e


    def get_inventory_by_product_id(self, product_id):
        try:
            self.cursor.execute("SELECT * FROM inventory WHERE product_id=?", (product_id,))
            inventory = self.cursor.fetchall()
            return inventory
        except sqlite3.Error as e:
            raise Exception("Error al obtener el inventario por ID de producto.") from e

    def insert_product(self, code, name, lot, location, quantity):
        try:
            self.cursor.execute("INSERT INTO products (code, name, lot, location, quantity) VALUES (?, ?, ?, ?, ?)",
                           (code, name, lot, location, quantity))
            self.connection.commit()
        except sqlite3.IntegrityError as e:
            raise Exception("Error de integridad al insertar el producto: El código de producto ya existe en la base de datos.") from e
        except sqlite3.Error as e:
            raise Exception("Error al insertar el producto.") from e

    def update_product_location_quantity(self, id, new_location, new_quantity):
        try:
            self.cursor.execute("UPDATE products SET location=?, quantity=? WHERE id=?", (new_location, new_quantity, id))
            self.connection.commit()
        except sqlite3.IntegrityError as e:
            raise Exception("Error de integridad al actualizar el producto: El código de producto ya existe en la base de datos.") from e
        except sqlite3.Error as e:
            raise Exception("Error al actualizar la información del producto.") from e

    def delete_product(self, id):
        try:
            self.cursor.execute("DELETE FROM products WHERE id=?", (id,))
            self.connection.commit()
        except sqlite3.IntegrityError as e:
            raise Exception("Error de integridad al eliminar el producto: El código de producto no existe en la base de datos.") from e
        except sqlite3.Error as e:
            raise Exception("Error al eliminar el producto.") from e

    def search_product(self, name):
        try:
            self.cursor.execute("SELECT * FROM products WHERE name LIKE ?", ('%' + name + '%',))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            raise Exception("Error al buscar el producto.") from e


    def search_product_by_fields(self, query):
        try:
            search_query = '%' + query + '%'
            self.cursor.execute("SELECT * FROM products WHERE "
                                "code LIKE ? OR "
                                "name LIKE ? OR "
                                "lot LIKE ? OR "
                                "location LIKE ? OR "
                                "quantity LIKE ?",
                                (search_query, search_query, search_query, search_query, search_query))
            products = self.cursor.fetchall()
            return products
        except sqlite3.Error as e:
            raise Exception("Error al buscar el producto por campos.") from e


    def get_products(self):
        try:
            self.cursor.execute("SELECT * FROM products")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            raise Exception("Error al obtener todos los productos.") from e
        return []

    def get_product_by_id(self, product_id):
        try:
            self.cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
            product = self.cursor.fetchone()
            return product
        except sqlite3.Error as e:
            raise Exception("Error al obtener el producto por ID.") from e

    def count_products_by_id(self, product_id):
        try:
            self.cursor.execute("SELECT COUNT(*) FROM products WHERE id=?", (product_id,))
            count = self.cursor.fetchone()[0]
            return count
        except sqlite3.Error as e:
            raise Exception("Error al contar los productos por ID.") from e

    def create_product_counts_table(self):
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS product_counts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    count INTEGER,
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')
            self.connection.commit()
        except sqlite3.Error as e:
            raise Exception("Error al crear la tabla de conteo de productos.") from e

    def insert_product_count(self, product_id, count):
        try:
            self.cursor.execute("INSERT INTO product_counts (product_id, count) VALUES (?, ?)", (product_id, count))
            self.connection.commit()
        except sqlite3.IntegrityError as e:
            raise Exception("Error de integridad al insertar el conteo del producto.") from e
        except sqlite3.Error as e:
            raise Exception("Error al insertar el conteo del producto.") from e

    def get_product_count(self, product_id):
        try:
            self.cursor.execute("SELECT count FROM product_counts WHERE product_id=?", (product_id,))
            count = self.cursor.fetchone()
            return count[0] if count else 0
        except sqlite3.Error as e:
            raise Exception("Error al obtener el conteo del producto.") from e



    def import_data_csv(self, csv_file_path):
        imported_count = 0  # Inicializa un contador para el número de registros importados
        try:
            with open(csv_file_path, mode='r', encoding='utf-8') as file:
                csv_reader = csv.reader(file, delimiter=',')  # Usar ',' como delimitador para separar las columnas
                headers = next(csv_reader)  # Omitir la fila de encabezado

                for row in csv_reader:
                    # Verificar que la fila tenga al menos 5 valores (columnas)
                    if len(row) >= 5:
                        # Extraer datos de la fila del CSV
                        code, name, lot, location, quantity = row

                        # Comprobar si la tabla está vacía
                        if not self.is_table_empty():
                            # Verificar si ya existe un registro idéntico en la tabla
                            if self.has_identical_record(code, name, lot, location, quantity):
                                continue  # Saltar esta fila si ya existe un registro idéntico

                        # Insertar los datos ya que es una nueva entrada o la tabla está vacía
                        self.insert_product(code, name, lot, location, quantity)
                        imported_count += 1  # Incrementa el contador de registros importados

                self.connection.commit()
        except sqlite3.Error as e:
            raise Exception("Error al importar los datos desde el archivo CSV.") from e

        return imported_count  # Devuelve el contador de registros importados


    def is_table_empty(self):
        try:
            self.cursor.execute("SELECT COUNT(*) FROM products")
            count = self.cursor.fetchone()[0]
            return count == 0
        except sqlite3.Error as e:
            raise Exception("Error al verificar si la tabla está vacía.") from e

    def has_identical_record(self, code, name, lot, location, quantity):
        try:
            self.cursor.execute("SELECT * FROM products WHERE code=? AND name=? AND lot=? AND location=? AND quantity=?",
                                (code, name, lot, location, quantity))
            return self.cursor.fetchone() is not None
        except sqlite3.Error as e:
            raise Exception("Error al verificar si existe un registro idéntico.") from e


#--------------------------------------------------# PAGE BASE #--------------------------------------------------#

class PageBase(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)


#--------------------------------------------------# PAGE HOME #--------------------------------------------------#

class HomePage(PageBase):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()

        # Agregar una etiqueta para la imagen
        image_label = QLabel(self)
        pixmap = QPixmap(LOGO_HOME)  
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(image_label)

        # Agregar un mensaje de bienvenida
        welcome_label = QLabel("¡Bienvenido al sistema!")
        welcome_label.setFont(QFont('Arial', 18))
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(welcome_label)

        # Agregar un espacio vertical para separar la imagen y los iconos
        self.layout.addSpacing(20)  # Ajusta el valor según tus preferencias

        # Crear un contenedor horizontal para los iconos
        icon_layout = QHBoxLayout()

        # Agregar iconos con enlaces
        self.add_icon_button(icon_layout, ICON_GITHUB, self.open_github)
        self.add_icon_button(icon_layout, ICON_LINKEDIN, self.open_linkedin)
        self.add_icon_button(icon_layout, ICON_FACEBOOK, self.open_facebook)
        self.add_icon_button(icon_layout, ICON_YOUTUBE, self.open_youtube)


        # Alinear los iconos en la parte inferior izquierda
        icon_layout.addStretch(1)  # Empuja los iconos a la izquierda
        self.layout.addLayout(icon_layout)

        self.setLayout(self.layout)

    def add_icon_button(self, layout, icon_path, click_handler):
        icon_button = QPushButton()
        icon = QIcon(icon_path)
        icon_button.setIcon(icon)
        icon_button.setIconSize(QSize(25, 25))  # Ajusta el tamaño del icono según tus preferencias
        icon_button.clicked.connect(click_handler)
        layout.addWidget(icon_button)


    def open_facebook(self):
        # Abre la página de Facebook en un navegador web
        facebook_url = "https://www.facebook.com/profile.php?id=100063571989268"
        QDesktopServices.openUrl(QUrl(facebook_url))

    def open_youtube(self):
        # Abre la página de YouTube en un navegador web
        youtube_url = "https://www.youtube.com/channel/UCkUO8a7Cv2cI-S_fTyGPLQg"
        QDesktopServices.openUrl(QUrl(youtube_url))

    def open_github(self):
        # Abre la página de GitHub en un navegador web
        github_url = "https://github.com/john-acha/"
        QDesktopServices.openUrl(QUrl(github_url))

    def open_linkedin(self):
        # Abre la página de LinkedIn en un navegador web
        linkedin_url = "https://www.linkedin.com/in/john-acha-jimenez"
        QDesktopServices.openUrl(QUrl(linkedin_url))


#--------------------------------------------------# PAGE REGISTER #--------------------------------------------------#
class RegisterProductPage(PageBase):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DatabaseManager(DATABASE_NAME) 
        # Crear un layout vertical principal

        register_layout = QVBoxLayout(self)
        # Título de la página
        title_label = QLabel('REGISTRAR PRODUCTO')
        title_label.setFont(QFont('Arial', 16))

        register_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        # Grupo de widgets para los campos de registro
        register_group = QGroupBox('Datos del Producto a Registrar')
        # Layout de formulario para los campos
        form_layout = QFormLayout()
        # Campo para ingresar el código del producto
        self.code_register_edit = QLineEdit()
        self.name_register_edit = QLineEdit()
        self.lot_register_edit = QLineEdit()
        self.location_register_edit = QLineEdit()
        self.quantity_register_edit = QLineEdit()
        form_layout.addRow('Código:', self.code_register_edit)
        form_layout.addRow('Descripción:', self.name_register_edit)
        form_layout.addRow('Lote:', self.lot_register_edit)
        form_layout.addRow('Ubicación:', self.location_register_edit)
        form_layout.addRow('Cantidad:', self.quantity_register_edit)
        register_group.setLayout(form_layout)
        # Botón para realizar el registro
        register_button = QPushButton('Registrar Producto')

        # ICONO REGISTRAR PRODUCTO
        register_button.setIcon(QIcon(os.path.join(basedir, "icons", "register.svg")))


        register_button.clicked.connect(self.register_product)
        button_layout = QHBoxLayout()
        button_layout.addWidget(register_button, alignment=Qt.AlignmentFlag.AlignCenter)
        # Agregar el grupo de campos y el botón al layout principal
        register_layout.addWidget(register_group)
        register_layout.addLayout(button_layout)

    # Funcionalidad de la pagina Registrar Productos
    def register_product(self):
        # Obtener los valores ingresados por el usuario
        code = self.code_register_edit.text().upper()
        name = self.name_register_edit.text().upper()
        lot = self.lot_register_edit.text().upper()
        location = self.location_register_edit.text().upper()
        quantity = self.quantity_register_edit.text()
        
        # Verificar si algún campo está vacío
        if not code or not name or not lot or not location or not quantity:
            QtWidgets.QMessageBox.critical(self, 'Error de Registro', 'Todos los campos deben estar llenos.')
            return

        quantity_text = self.quantity_register_edit.text()
        
        try:
            quantity = int(quantity_text)
            if quantity < 0:
                raise ValueError("La cantidad debe ser mayor o igual a cero ")
        except ValueError:
            QMessageBox.warning(self, "Valor no válido", "El campo 'Cantidad' debe ser un número entero válido.")
            return

        # Intentar registrar el producto en la base de datos
        try:
            self.db_manager.insert_product(code, name, lot, location, quantity)
            self.db_manager.connection.commit()
            registration = True
        except Exception as e:
            registration = False
            QtWidgets.QMessageBox.critical(self, 'Error de Registro', f'Hubo un error al registrar el producto: {str(e)}')

        # Mostrar un mensaje de éxito o error en función del resultado
        if registration:
            QtWidgets.QMessageBox.information(self, 'Registro Exitoso', 'El producto se registró con éxito.')
        else:
            QtWidgets.QMessageBox.critical(self, 'Error de Registro', 'Hubo un error al registrar el producto.')

        # Limpia los campos después del registro
        self.code_register_edit.clear()
        self.name_register_edit.clear()
        self.lot_register_edit.clear()
        self.location_register_edit.clear()
        self.quantity_register_edit.clear()

#--------------------------------------------------# PAGE UPDATE #--------------------------------------------------#


class UpdateProductPage(PageBase):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DatabaseManager(DATABASE_NAME)

        main_layout = QVBoxLayout(self)
        title_label = QLabel('ACTUALIZAR PRODUCTO')
        title_label.setFont(QFont('Arial', 16))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        update_group = QGroupBox('Actualizar Producto Existente')
        form_layout = QFormLayout()

        # Campo para ingresar el ID del producto a actualizar
        self.id_update_edit = QLineEdit()
        form_layout.addRow('ID del producto:', self.id_update_edit)

        # Botón para buscar y cargar el producto
        load_button = QPushButton('Cargar Producto')

        # ICONO CARGAR PRODUCTO
        load_button.setIcon(QIcon(os.path.join(basedir, "icons", "load.svg")))


        load_button.clicked.connect(self.load_product)
        form_layout.addRow('', load_button)

        # Campos de edición para los atributos del producto
        self.code_update_edit = QLineEdit()
        self.name_update_edit = QLineEdit()
        self.lot_update_edit = QLineEdit()
        self.location_update_edit = QLineEdit()
        self.quantity_update_edit = QLineEdit()

        form_layout.addRow('Código:', self.code_update_edit)
        form_layout.addRow('Descripción:', self.name_update_edit)
        form_layout.addRow('Lote:', self.lot_update_edit)
        form_layout.addRow('Ubicación:', self.location_update_edit)
        form_layout.addRow('Cantidad:', self.quantity_update_edit)

        update_group.setLayout(form_layout)
        main_layout.addWidget(update_group)

        # Botón para guardar los cambios
        update_button = QPushButton('Guardar Cambios')

        # ICONO ACTUALIZAR PRODUCTO
        update_button.setIcon(QIcon(os.path.join(basedir, "icons", "save.svg")))

        update_button.clicked.connect(self.update_product)
        main_layout.addWidget(update_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Inicialmente, deshabilita los campos de edición y el botón de guardar
        self.disable_edit_fields()

    def load_product(self):
        id = self.id_update_edit.text().strip()

        if not id:
            QMessageBox.warning(self, "Campo vacío", "Por favor, ingrese un ID de producto.")
            return

        try:
            product = self.db_manager.get_product_by_id(id)
            if product:
                # Mostrar los atributos del producto en los campos de edición
                self.code_update_edit.setText(product[1])
                self.name_update_edit.setText(product[2])
                self.lot_update_edit.setText(product[3])
                self.location_update_edit.setText(product[4])
                self.quantity_update_edit.setText(str(product[5]))
                # Deshabilitar los campos de código, descripción y lote
                self.id_update_edit.setDisabled(True)
                self.code_update_edit.setDisabled(True)
                self.name_update_edit.setDisabled(True)
                self.lot_update_edit.setDisabled(True)
                # Habilitar los campos de edición de ubicación y cantidad
                self.enable_edit_fields()
            else:
                QMessageBox.warning(self, "Producto no encontrado", f"No se encontró ningún producto con el ID {id}.")
                # Limpia los campos de edición y deshabilita los campos
                self.clear_edit_fields()
                self.disable_edit_fields()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar el producto: {str(e)}")

    def update_product(self):
        id = self.id_update_edit.text().strip()
        location = self.location_update_edit.text().strip()
        quantity_text = self.quantity_update_edit.text().strip()

        if not id or not location or not quantity_text:
            QMessageBox.warning(self, "Campos vacíos", "Todos los campos deben estar llenos.")
            return

        try:
            quantity = int(quantity_text)
            if quantity < 0:
                QMessageBox.warning(self, "Valor no válido", "El campo 'Cantidad' debe ser mayor o igual a cero.")
                return
        except ValueError:
            QMessageBox.warning(self, "Valor no válido", "El campo 'Cantidad' debe ser un número entero válido.")
            return

        try:
            self.db_manager.update_product_location_quantity(id, location, quantity)
            # Limpia los campos de edición y deshabilita los campos
            self.clear_edit_fields()
            self.disable_edit_fields()
            QMessageBox.information(self, "Actualización Exitosa", "Los cambios se guardaron con éxito.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al actualizar el producto: {str(e)}")

    def clear_edit_fields(self):
        self.id_update_edit.clear()
        self.code_update_edit.clear()
        self.name_update_edit.clear()
        self.lot_update_edit.clear()
        self.location_update_edit.clear()
        self.quantity_update_edit.clear()

    def disable_edit_fields(self):
        self.id_update_edit.setDisabled(False)  # Habilitar el campo de ID
        self.code_update_edit.setDisabled(True)
        self.name_update_edit.setDisabled(True)
        self.lot_update_edit.setDisabled(True)
        self.location_update_edit.setDisabled(True)
        self.quantity_update_edit.setDisabled(True)

    def enable_edit_fields(self):
        self.location_update_edit.setDisabled(False)
        self.quantity_update_edit.setDisabled(False)

#--------------------------------------------------# PAGE DELETE #--------------------------------------------------#

class DeleteProductPage(PageBase):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DatabaseManager(DATABASE_NAME)

        main_layout = QVBoxLayout(self)
        title_label = QLabel('ELIMINAR PRODUCTO')
        title_label.setFont(QFont('Arial', 16))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        search_group = QGroupBox('Buscar Producto a Eliminar')
        search_layout = QFormLayout()

        # Campo para ingresar el nombre del producto a eliminar
        self.name_delete_edit = QLineEdit()

        # Conectar la señal textChanged al método clear_search_results_and_model
        self.name_delete_edit.textChanged.connect(self.clear_search_results_and_model)

        search_layout.addRow('Nombre del producto:', self.name_delete_edit)

        # Botón para buscar el producto
        search_button = QPushButton('Buscar')

        # ICONO BUSCAR PRODUCTO
        search_button.setIcon(QIcon(os.path.join(basedir, "icons", "search.svg")))


        search_button.clicked.connect(self.search_result_list)
        search_layout.addRow('', search_button)

        search_group.setLayout(search_layout)
        main_layout.addWidget(search_group)

        # Resultados de la búsqueda
        search_result = QLabel('Resultado de la Búsqueda:')
        main_layout.addWidget(search_result)

        # Crear un nuevo QStandardItemModel para los resultados de la búsqueda
        self.search_model = QStandardItemModel()
        self.search_model.setHorizontalHeaderLabels(["ID", "CÓDIGO", "DESCRIPCIÓN", "LOTE", "UBICACIÓN", "CANTIDAD"])

        # Lista o vista de resultados de la búsqueda
        self.search_result_list = QTreeView()
        self.search_result_list.setModel(self.search_model)
        main_layout.addWidget(self.search_result_list)

        # Botón para eliminar el producto seleccionado (inicialmente deshabilitado)
        self.delete_button = QPushButton('Eliminar Producto')


        # ICONO ELIMINAR PRODUCTO
        self.delete_button.setIcon(QIcon(os.path.join(basedir, "icons", "delete.svg")))

        
        self.delete_button.clicked.connect(self.delete_selected_product)
        self.delete_button.setEnabled(False)  # Deshabilitar el botón por defecto
        main_layout.addWidget(self.delete_button)

        # Conectar la señal de selección del QTreeView a la función para habilitar el botón
        self.search_result_list.selectionModel().selectionChanged.connect(self.enable_delete_button)

    def enable_delete_button(self):
        # Habilitar el botón de eliminación si hay un elemento seleccionado en el QTreeView
        selected_index = self.search_result_list.selectionModel().currentIndex()
        self.delete_button.setEnabled(selected_index.isValid())

    def clear_search_results_and_model(self):
        # Esta función se llamará cuando el texto en el campo de búsqueda cambie o se borre
        self.search_model.removeRows(0, self.search_model.rowCount())

    def search_result_list(self):
        name = self.name_delete_edit.text().strip()

        if not name:
            # Si el campo de búsqueda está vacío, limpiar el QTreeView y el modelo
            self.clear_search_results_and_model()
            return

        try:
            # Realizar una consulta SQL para buscar productos que coincidan con el nombre
            products = self.db_manager.search_product(name)

            # Limpiar la lista de resultados de la búsqueda y el modelo
            self.clear_search_results_and_model()

            if products:
                # Agregar los resultados de la búsqueda al QStandardItemModel
                for product in products:
                    row = [str(item) for item in product]
                    items = [QStandardItem(item) for item in row]

                    # Alinear a la derecha las columnas "ID" y "Cantidad"
                    items[0].setTextAlignment(Qt.AlignmentFlag.AlignRight)
                    items[5].setTextAlignment(Qt.AlignmentFlag.AlignRight)

                    self.search_model.appendRow(items)

            else:
                QMessageBox.information(self, "Búsqueda sin resultados", "No se encontraron productos con ese nombre.")
        except Exception as e:
            QMessageBox.critical(self, "Error de Búsqueda", f"Error al buscar productos: {str(e)}")

    def delete_selected_product(self):
        selected_index = self.search_result_list.selectionModel().currentIndex()

        if selected_index.isValid():
            # Obtener el ID del producto seleccionado
            id = self.search_model.item(selected_index.row(), 0).text()

            # Mostrar un cuadro de diálogo de confirmación
            confirm_dialog = QMessageBox()
            confirm_dialog.setIcon(QMessageBox.Question)
            confirm_dialog.setWindowTitle("Confirmación de Eliminación")
            confirm_dialog.setText(f"¿Está seguro de que desea eliminar el producto con ID {id}?")
            confirm_dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            confirm_dialog.setDefaultButton(QMessageBox.No)

            result = confirm_dialog.exec_()

            if result == QMessageBox.Yes:
                try:
                    # Eliminar el producto de la base de datos
                    self.db_manager.delete_product(id)
                    self.db_manager.connection.commit()
                    QMessageBox.information(self, "Eliminación Exitosa", "El producto se eliminó con éxito.")
                    # Limpiar la lista de resultados después de la eliminación y el modelo
                    self.clear_search_results_and_model()
                except Exception as e:
                    QMessageBox.critical(self, "Error al Eliminar", f"Error al eliminar el producto: {str(e)}")
            else:
                # El usuario seleccionó "No", no se realiza ninguna acción
                pass
        else:
            QMessageBox.warning(self, "Producto no seleccionado", "Por favor, seleccione un producto para eliminar.")


#--------------------------------------------------# PAGE SEARCH #--------------------------------------------------#
class SearchProductPage(PageBase):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DatabaseManager(DATABASE_NAME)
        # Crear un layout vertical principal
        main_layout = QVBoxLayout(self)
        # Título de la página
        title_label = QLabel('BUSCAR PRODUCTO')
        title_label.setFont(QFont('Arial', 16))
        main_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Grupo de widgets para los campos de búsqueda
        search_group = QGroupBox('Búsqueda de Producto')
        # Layout de formulario para los campos de búsqueda
        form_layout = QFormLayout()

        # Etiqueta y campo de búsqueda
        search_label = QLabel('Nombre del producto a buscar:')
        self.name_search_edit = QLineEdit()
        form_layout.addRow(search_label, self.name_search_edit)

        # Botón de búsqueda
        search_button = QPushButton('Buscar')


        # ICONO BUSCAR PRODUCTO
        search_button.setIcon(QIcon(os.path.join(basedir, "icons", "search.svg")))


        search_button.clicked.connect(self.perform_search)
        form_layout.addRow('', search_button)  # Agregar el botón a la misma fila

        # Establecer el layout de formulario en el grupo de búsqueda
        search_group.setLayout(form_layout)

        # TreeView para mostrar los resultados de la búsqueda
        self.search_tree_view = QTreeView()

        # Agregar el grupo de búsqueda y el TreeView al layout principal
        main_layout.addWidget(search_group)
        main_layout.addWidget(self.search_tree_view)

        # Crear un nuevo QStandardItemModel para los resultados de la búsqueda
        self.search_model = QStandardItemModel()
        self.search_model.setHorizontalHeaderLabels(["ID", "Código", "Descripción", "Lote", "Ubicación", "Cantidad"])
        self.search_tree_view.setModel(self.search_model)
        header = self.search_tree_view.header()
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

        # Conectar la señal textChanged del QLineEdit al método de limpiar el QTreeView
        self.name_search_edit.textChanged.connect(self.clear_results)

    def clear_results(self):
        # Esta función se llamará cada vez que el texto en el campo de búsqueda cambie
        name = self.name_search_edit.text().strip()

        if not name:
            # Si el campo de búsqueda está vacío, limpiar el QTreeView
            self.search_model.removeRows(0, self.search_model.rowCount())


    def perform_search_by_fields(self, query):
        try:
            # Realizar una consulta SQL para buscar productos que coincidan con la consulta
            products = self.db_manager.search_product_by_fields(query)

            # Limpiar la lista de resultados de la búsqueda
            self.clear_results()

            if products:
                # Agregar los resultados de la búsqueda al QStandardItemModel
                for product in products:
                    row = [str(item) for item in product]
                    items = [QStandardItem(item) for item in row]

                    # Alinear a la derecha las columnas "ID" y "Cantidad"
                    items[0].setTextAlignment(Qt.AlignmentFlag.AlignRight)
                    items[5].setTextAlignment(Qt.AlignmentFlag.AlignRight)

                    self.search_model.appendRow(items)

            else:
                QMessageBox.information(self, "Búsqueda sin resultados", "No se encontraron productos con esa consulta.")
        except Exception as e:
            QMessageBox.critical(self, "Error de Búsqueda", f"Error al buscar productos: {str(e)}")


    def perform_search(self):
        # Obtener el valor de búsqueda ingresado por el usuario
        query = self.name_search_edit.text().upper()

        # Verificar si el campo de búsqueda está vacío
        if not query:
            QMessageBox.warning(self, "Campo vacío", "Por favor, ingrese una consulta para buscar.")
            return  # Salir de la función si el campo está vacío

        # Llamar al nuevo método para realizar la búsqueda
        self.perform_search_by_fields(query)


#--------------------------------------------------# PAGE VIEW #--------------------------------------------------#


class ViewProductPage(PageBase):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DatabaseManager(DATABASE_NAME)

        # Diseño de la interfaz
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)  # Establecer los márgenes a 0

        title_label = QLabel('LISTA DE PRODUCTOS')
        title_label.setFont(QFont('Arial', 16))

        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # Botón de refresco
        refresh_button = QPushButton('Refrescar')

        # ICONO REFRESCAR PRODUCTO
        refresh_button.setIcon(QIcon(os.path.join(basedir, "icons", "refresh.svg")))

        refresh_button.clicked.connect(self.refresh_table)
        main_layout.addWidget(refresh_button, alignment=Qt.AlignmentFlag.AlignRight)


        # Crear un área de desplazamiento para la tabla
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # Hace que el contenido se ajuste automáticamente al tamaño del área
        main_layout.addWidget(scroll_area)

        # Crear una tabla para mostrar los productos dentro del área de desplazamiento
        self.table = QTableWidget()
        self.table.setColumnCount(6)  # 6 columnas para ID, Código, Nombre, Lote, Ubicación y Cantidad

        # Definir los encabezados de las columnas
        headers = ["ID", "Código", "Descripción", "Lote", "Ubicación", "Cantidad"]
        self.table.setHorizontalHeaderLabels(headers)

        # Ajustar el tamaño de las columnas para que se ajusten al contenido
        self.table.horizontalHeader().setStretchLastSection(True)

        # Centrar los títulos de las columnas
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

        # Ajustar el tamaño de las columnas específicas
        # self.table.setColumnWidth(0, 40)  # Columna ID más pequeña
        # self.table.setColumnWidth(2, 400)  # Columna Nombre más grande
        # self.table.setColumnWidth(5, 100)  # Columna Nombre más grande
        # Establecer la tabla como el widget contenido en el área de desplazamiento
        scroll_area.setWidget(self.table)

        # Llama al método refresh_table para cargar los datos al inicio de la aplicación
        self.refresh_table()

    def refresh_table(self):
        # Obtener la lista de productos actualizada desde la base de datos y actualizar la tabla
        try:
            products = self.db_manager.get_products()
            self.fill_table(products)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al refrescar la tabla: {str(e)}")

    def fill_table(self, products):
        # Limpiar la tabla antes de llenarla nuevamente
        self.table.setRowCount(0)

        # Llenar la tabla con los datos de los productos
        for product in products:
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)

            # Insertar los datos en las celdas de la fila
            for col_index, data in enumerate(product):
                item = QTableWidgetItem(str(data))
                self.table.setItem(row_position, col_index, item)

                # Alinear las columnas numéricas a la derecha

                # Alinear las columnas numéricas a la derecha
                if col_index in [0, 5]:  # Columna ID y Cantidad
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight)



#--------------------------------------------------# PAGE TOOL #--------------------------------------------------#


class GenerateQRPage(PageBase):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DatabaseManager(DATABASE_NAME)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Generador de Códigos QR')

        main_layout = QVBoxLayout(self)

        title_label = QLabel('GENERAR QR')
        title_label.setFont(QtGui.QFont('Arial', 16))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        sections_layout = QHBoxLayout()

        left_layout = QVBoxLayout()

        id_section = QGroupBox('Buscar por ID:')
        id_layout = QVBoxLayout()

        id_label = QLabel('Ingrese el ID del producto:')
        self.id_edit = QLineEdit()

        id_layout.addWidget(id_label)
        id_layout.addWidget(self.id_edit)

        load_button = QPushButton('Cargar Datos')

        # ICONO CARGAR PRODUCTO
        load_button.setIcon(QIcon(os.path.join(basedir, "icons", "load.svg")))

        load_button.clicked.connect(self.load_data)
        id_layout.addWidget(load_button)

        id_section.setLayout(id_layout)
        left_layout.addWidget(id_section)

        left_section = QGroupBox('Seleccione los datos:')
        form_layout = QFormLayout()

        self.checkbox_id = QCheckBox('ID:')
        self.id_edit_new = QLineEdit()
        self.checkbox_code = QCheckBox('Código:')
        self.code_edit = QLineEdit()
        self.checkbox_name = QCheckBox('Descripción:')
        self.name_edit = QLineEdit()
        self.checkbox_lot = QCheckBox('Lote:')
        self.lot_edit = QLineEdit()
        self.checkbox_location = QCheckBox('Ubicación:')
        self.location_edit = QLineEdit()
        self.checkbox_quantity = QCheckBox('Cantidad:')
        self.quantity_edit = QLineEdit()

        form_layout.addRow(self.checkbox_id)
        form_layout.addRow(self.id_edit_new)
        form_layout.addRow(self.checkbox_code)
        form_layout.addRow(self.code_edit)
        form_layout.addRow(self.checkbox_name)
        form_layout.addRow(self.name_edit)
        form_layout.addRow(self.checkbox_lot)
        form_layout.addRow(self.lot_edit)
        form_layout.addRow(self.checkbox_location)
        form_layout.addRow(self.location_edit)
        form_layout.addRow(self.checkbox_quantity)
        form_layout.addRow(self.quantity_edit)

        left_section.setLayout(form_layout)
        left_layout.addWidget(left_section)

        sections_layout.addLayout(left_layout)

        right_section = QGroupBox('Vista previa del QR:')
        right_layout = QVBoxLayout(right_section)

        self.qr_pixmap_item = QGraphicsPixmapItem()
        qr_scene = QGraphicsScene()
        qr_scene.addItem(self.qr_pixmap_item)
        self.qr_view = QGraphicsView(qr_scene)
        self.qr_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        #self.qr_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.qr_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)


        save_button = QPushButton('Guardar Código QR')
        
        # ICONO GUARDAR QR PRODUCTO
        save_button.setIcon(QIcon(os.path.join(basedir, "icons", "save.svg")))
        
        
        save_button.clicked.connect(self.save_qr)

        right_layout.addWidget(self.qr_view)
        right_layout.addWidget(save_button, alignment=Qt.AlignmentFlag.AlignCenter)

        sections_layout.addWidget(right_section)
        main_layout.addLayout(sections_layout)
        self.setLayout(main_layout)

        self.id_edit.textChanged.connect(self.clear_input_entries)
        self.checkbox_id.stateChanged.connect(self.update_qr)
        self.checkbox_code.stateChanged.connect(self.update_qr)
        self.checkbox_name.stateChanged.connect(self.update_qr)
        self.checkbox_lot.stateChanged.connect(self.update_qr)
        self.checkbox_location.stateChanged.connect(self.update_qr)
        self.checkbox_quantity.stateChanged.connect(self.update_qr)



    def load_data(self):
        id = self.id_edit.text().strip()

        if not id:
            QMessageBox.warning(self, "Campo vacío", "Por favor, ingrese un ID.")
            return

        try:
            # Obtener datos del producto por ID desde la base de datos
            product = self.db_manager.get_product_by_id(id)

            if product:
                # Establecer valores en los campos de entrada
                self.id_edit_new.setText(str(product[0]))  # Agrega el ID al campo ID
                self.code_edit.setText(product[1])
                self.name_edit.setText(product[2])
                self.lot_edit.setText(product[3])
                self.location_edit.setText(product[4])
                self.quantity_edit.setText(str(product[5]))

                # Habilitar o deshabilitar casillas de verificación según los campos de entrada cargados
                self.checkbox_id.setEnabled(bool(product[0]))
                self.checkbox_code.setEnabled(bool(product[1]))
                self.checkbox_name.setEnabled(bool(product[2]))
                self.checkbox_lot.setEnabled(bool(product[3]))
                self.checkbox_location.setEnabled(bool(product[4]))
                self.checkbox_quantity.setEnabled(bool(product[5]))

                # Generar el código QR después de cargar los datos
                self.update_qr()
            else:
                QMessageBox.warning(self, "Producto no encontrado", f"No se encontró ningún producto con el ID {id}.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar los datos: {str(e)}")

    def clear_input_entries(self):
        if not self.id_edit.text().strip():
            # Borra los campos de entrada y habilita las casillas de verificación
            self.id_edit_new.clear()
            self.code_edit.clear()
            self.name_edit.clear()
            self.lot_edit.clear()
            self.location_edit.clear()
            self.quantity_edit.clear()
            self.checkbox_id.setChecked(False)
            self.checkbox_code.setChecked(False)
            self.checkbox_name.setChecked(False)
            self.checkbox_lot.setChecked(False)
            self.checkbox_location.setChecked(False)
            self.checkbox_quantity.setChecked(False)
            self.qr_pixmap_item.setPixmap(QPixmap())  # Limpia la vista previa del código QR

    def update_qr(self):
        # Verificar si al menos un campo de entrada contiene datos
        if (self.id_edit_new.text() or self.code_edit.text() or self.name_edit.text() or
                self.lot_edit.text() or self.location_edit.text() or self.quantity_edit.text()):
            # Construir el texto para el código QR en base a los checkboxes seleccionados
            qr_text = ''
            if self.checkbox_id.isChecked():
                # qr_text += f'ID: {self.id_edit_new.text()}\n'
                qr_text += f'{self.id_edit_new.text()}\n'
            if self.checkbox_code.isChecked():
                qr_text += f'Código: {self.code_edit.text()}\n'
            if self.checkbox_name.isChecked():
                qr_text += f'Descripción: {self.name_edit.text()}\n'
            if self.checkbox_lot.isChecked():
                qr_text += f'Lote: {self.lot_edit.text()}\n'
            if self.checkbox_location.isChecked():
                qr_text += f'Ubicación: {self.location_edit.text()}\n'
            if self.checkbox_quantity.isChecked():
                qr_text += f'Cantidad: {self.quantity_edit.text()}\n'

            # Generar el código QR y mostrarlo
            if qr_text:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(qr_text)
                qr.make(fit=True)

                img = qr.make_image(fill_color="black", back_color="white")
                buffer = BytesIO()
                img.save(buffer, format="PNG")

                pixmap = QPixmap()
                pixmap.loadFromData(buffer.getvalue())
                self.qr_pixmap_item.setPixmap(pixmap)
            else:
                self.qr_pixmap_item.setPixmap(QPixmap())  # Mostrar un QPixmap vacío si no hay datos
        else:
            self.qr_pixmap_item.setPixmap(QPixmap())  # Mostrar un QPixmap vacío si no hay datos

    def save_qr(self):
        qr_text = self.generate_qr_text()

        if not qr_text:
            QMessageBox.warning(self, "QR Vacío", "No hay código QR para guardar.")
            return

        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly  # Opcional: Hacer el cuadro de diálogo de solo lectura

        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar Código QR", "", "Imágenes (*.png);;Todos los archivos (*)", options=options)

        if file_path:
            try:
                self.save_qr_to_file(qr_text, file_path)
                QMessageBox.information(self, "Guardado Exitoso", f"Código QR guardado en {file_path}.")
            except Exception as e:
                QMessageBox.critical(self, "Error al Guardar", f"Error al guardar el código QR: {str(e)}")

    def generate_qr(self):
        # Verificar si hay datos cargados antes de generar el código QR
        if self.id_edit_new.text() or self.code_edit.text() or self.name_edit.text() or \
                self.lot_edit.text() or self.location_edit.text() or self.quantity_edit.text():
            # Construir el texto para el código QR en base a los checkboxes seleccionados
            qr_text = ''
            if self.checkbox_id.isChecked():
                qr_text += f'{self.id_edit_new.text()}\n'
                # qr_text += f'ID: {self.id_edit_new.text()}\n'
            if self.checkbox_code.isChecked():
                qr_text += f'Código: {self.code_edit.text()}\n'
            if self.checkbox_name.isChecked():
                qr_text += f'Descripción: {self.name_edit.text()}\n'
            if self.checkbox_lot.isChecked():
                qr_text += f'Lote: {self.lot_edit.text()}\n'
            if self.checkbox_location.isChecked():
                qr_text += f'Ubicación: {self.location_edit.text()}\n'
            if self.checkbox_quantity.isChecked():
                qr_text += f'Cantidad: {self.quantity_edit.text()}\n'

            # Generar el código QR y mostrarlo
            if qr_text:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(qr_text)
                qr.make(fit=True)

                img = qr.make_image(fill_color="black", back_color="white")
                buffer = BytesIO()
                img.save(buffer, format="PNG")

                pixmap = QPixmap()
                pixmap.loadFromData(buffer.getvalue())
                self.qr_pixmap_item.setPixmap(pixmap)
            else:
                self.qr_pixmap_item.setPixmap(QPixmap())  # Mostrar un QPixmap vacío si no hay datos
        else:
            self.qr_pixmap_item.setPixmap(QPixmap())  # Mostrar un QPixmap vacío si no hay datos

    def generate_qr_text(self):
        qr_text = ''
        if self.checkbox_id.isChecked():
            qr_text += f'{self.id_edit.text()}\n'
            # qr_text += f'ID: {self.id_edit.text()}\n'
        if self.checkbox_code.isChecked():
            qr_text += f'Código: {self.code_edit.text()}\n'
        if self.checkbox_name.isChecked():
            qr_text += f'Descripción: {self.name_edit.text()}\n'
        if self.checkbox_lot.isChecked():
            qr_text += f'Lote: {self.lot_edit.text()}\n'
        if self.checkbox_location.isChecked():
            qr_text += f'Ubicación: {self.location_edit.text()}\n'
        if self.checkbox_quantity.isChecked():
            qr_text += f'Cantidad: {self.quantity_edit.text()}\n'
        return qr_text

    def save_qr_to_file(self, qr_text, file_path):
        if qr_text:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_text)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            img.save(file_path, format="PNG", encoding="UTF-8")

#--------------------------------------------------# PAGE INVENTORY #--------------------------------------------------#



class InventoryProductPage(PageBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DatabaseManager(DATABASE_NAME)
        self.quantity_column_visible = False
        self.initUI()
        self.inventory_counts = {}  # Diccionario para hacer un seguimiento de las existencias
        
    
    def initUI(self):
        self.setWindowTitle('Inventario de Productos')

        main_layout = QVBoxLayout(self)

        title_label = QLabel('INVENTARIO DE PRODUCTOS')
        title_label.setFont(QFont('Arial', 16))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        form_layout = QVBoxLayout()

        id_label = QLabel('ID del Producto:')
        self.id_edit = QLineEdit()
        form_layout.addWidget(id_label)
        form_layout.addWidget(self.id_edit)

        product_location = QLabel('Ubicación Física del Producto:')
        self.product_location = QLineEdit()
        form_layout.addWidget(product_location)
        form_layout.addWidget(self.product_location)



        add_button = QPushButton('Agregar')

        # ICONO AGREGAR PRODUCTO
        add_button.setIcon(QIcon(os.path.join(basedir, "icons", "table.svg")))


        add_button.clicked.connect(self.add_product)
        form_layout.addWidget(add_button)

        main_layout.addLayout(form_layout)

        # Crear un widget contenedor para la tabla y el botón de exportación
        table_and_export_widget = QWidget()
        table_and_export_layout = QVBoxLayout(table_and_export_widget)

        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(8)

        headers = ["ID", "Código", "Descripción", "Lote", "Ubicación", "Cantidad", "Existencias", "Ubicación Física"]
        self.inventory_table.setHorizontalHeaderLabels(headers)


        # Configurar la visibilidad de la columna "Cantidad" al inicio (oculta)
        column_index = 5  # El índice de la columna "Cantidad" en la tabla
        self.inventory_table.setColumnHidden(column_index, not self.quantity_column_visible)


        table_and_export_layout.addWidget(self.inventory_table)

        # Boton para exportar a Excel
        export_button = QPushButton('Exportar datos')
        
        # ICONO EXPORTAR DATOS
        export_button.setIcon(QIcon(os.path.join(basedir, "icons", "excel.svg")))


        export_button.clicked.connect(self.export_to_excel)
        table_and_export_layout.addWidget(export_button)

        main_layout.addWidget(table_and_export_widget)

        
        # Configurar la visibilidad de la columna "Cantidad" al inicio (oculta)
        column_index = 5  # El índice de la columna "Cantidad" en la tabla
        self.inventory_table.setColumnHidden(column_index, not self.quantity_column_visible)

        # Crear un atajo para mostrar/ocultar la columna "Cantidad"
        #toggle_quantity_action = QAction("Mostrar/Ocultar Cantidad", self)
        #toggle_quantity_action.setShortcut("Q")  # Atajo "Q"
        #toggle_quantity_action.triggered.connect(self.toggle_quantity_column)

        # Agregar el atajo al menú
        #self.addAction(toggle_quantity_action)


        # Crear un atajo para mostrar/ocultar la columna "Cantidad"
        toggle_quantity_action = QAction("Mostrar/Ocultar Cantidad", self)
        toggle_quantity_action.setShortcut("Ctrl+Alt+Q")  # Atajo "Q"
        toggle_quantity_action.triggered.connect(self.toggle_quantity_column)

        # Agregar el atajo al menú
        self.addAction(toggle_quantity_action)


    def toggle_quantity_column(self):
        # Cambiar la visibilidad de la columna
        self.quantity_column_visible = not self.quantity_column_visible
        
        # Mostrar u ocultar la columna según el valor de self.quantity_column_visible
        column_index = 5  # El índice de la columna "Cantidad" en la tabla
        self.inventory_table.setColumnHidden(column_index, not self.quantity_column_visible)


    def export_to_excel(self):
        # Verificar si la tabla tiene datos
        if self.inventory_table.rowCount() == 0:
            QMessageBox.warning(self, 'Sin datos', 'La tabla está vacía. No hay datos para exportar a Excel.')
            return

        # El resto del código para la exportación a Excel
        table_data = []
        headers = []
        for col in range(self.inventory_table.columnCount()):
            headers.append(self.inventory_table.horizontalHeaderItem(col).text())
        table_data.append(headers)
        for row in range(self.inventory_table.rowCount()):
            row_data = []
            for col in range(self.inventory_table.columnCount()):
                item = self.inventory_table.item(row, col)
                if item:
                    # Verificar si la columna es ID, Cantidad o Existencias y convertir a número si es necesario
                    if col in [0, 5, 6]:
                        try:
                            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignCenter)  # Alineación a la derecha y centrado vertical
                            row_data.append(float(item.text()))
                        except ValueError:
                            # En caso de error al convertir, mantener el valor original como texto
                            row_data.append(item.text())
                    else:
                        row_data.append(item.text())
                else:
                    row_data.append('')
            table_data.append(row_data)

        # Crear un archivo de Excel y escribir los datos
        wb = Workbook()
        ws = wb.active
        for row in table_data:
            ws.append(row)

        # Obtener la ruta del archivo Excel donde se guardará
        file_path, _ = QFileDialog.getSaveFileName(self, 'Guardar como archivo Excel', '', 'Excel Files (*.xlsx)')
        if file_path:
            # Guardar el archivo Excel
            wb.save(file_path)

            # Mostrar un mensaje de éxito
            QMessageBox.information(self, 'Exportación exitosa', 'Los datos se exportaron a Excel correctamente.')




    
    def change_cursor_to_hand(self):
        # This method is connected to the hovered signal of the "Agregar" button
        self.sender().setCursor(QCursor(Qt.PointingHandCursor))



    def add_product(self):
        product_id = self.id_edit.text()
        product_location = self.product_location.text()  # Obtener la ubicación física

        if not product_id:
            QMessageBox.warning(self, "Campo Vacío", "Por favor, escanee el código QR del producto.")
            return

        try:
            # Obtener los datos del producto por ID desde la base de datos
            product = self.db_manager.get_product_by_id(product_id)

            if product:
                # Obtener la cantidad de veces que se ha ingresado este ID
                existencias = self.inventory_counts.get(product_id, 0)
                existencias += 1

                # Actualizar el contador en el diccionario
                self.inventory_counts[product_id] = existencias

                # Buscar si el ID ya existe en la tabla y actualizar el contador
                for row in range(self.inventory_table.rowCount()):
                    id_item = self.inventory_table.item(row, 0)
                    if id_item and id_item.text() == product_id:
                        existencias_item = self.inventory_table.item(row, 6)
                        if existencias_item:
                            existencias_item.setText(str(existencias))
                        ubicacion_fisica_item = self.inventory_table.item(row, 7)  # Obtener la celda de ubicación física
                        if ubicacion_fisica_item:
                            ubicacion_fisica_item.setText(product_location)  # Establecer la ubicación física
                        break
                else:
                    # Si el ID no existe en la tabla, agregar un nuevo registro
                    row_position = self.inventory_table.rowCount()
                    self.inventory_table.insertRow(row_position)
                    for col, data in enumerate(product):
                        item = QTableWidgetItem(str(data))
                        if col in [0, 5, 6]:
                            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                        self.inventory_table.setItem(row_position, col, item)
                    existencias_item = QTableWidgetItem(str(existencias))
                    existencias_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.inventory_table.setItem(row_position, 6, existencias_item)
                    ubicacion_fisica_item = QTableWidgetItem(product_location)  # Crear celda para ubicación física
                    self.inventory_table.setItem(row_position, 7, ubicacion_fisica_item)  # Establecer ubicación física

                # Limpiar las entradas del ID y la ubicación física
                self.id_edit.clear()
                self.product_location.clear()
                
                # Establecer el foco de nuevo en el campo de entrada de ID
                self.id_edit.setFocus()
            else:
                # El producto no se encontró en la base de datos
                QMessageBox.warning(self, "Producto no encontrado", f"No se encontró ningún producto con el ID {product_id}.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al agregar el producto: {str(e)}")



    def add_product_OLD(self):
        product_id = self.id_edit.text()

        if not product_id:
            QMessageBox.warning(self, "Campo Vacío", "Por favor, escanee el código QR del producto.")
            return

        try:
            # Obtener los datos del producto por ID desde la base de datos
            product = self.db_manager.get_product_by_id(product_id)

            if product:
                # Obtener la cantidad de veces que se ha ingresado este ID
                existencias = self.inventory_counts.get(product_id, 0)
                existencias += 1

                # Actualizar el contador en el diccionario
                self.inventory_counts[product_id] = existencias

                # Buscar si el ID ya existe en la tabla y actualizar el contador
                for row in range(self.inventory_table.rowCount()):
                    id_item = self.inventory_table.item(row, 0)
                    if id_item and id_item.text() == product_id:
                        existencias_item = self.inventory_table.item(row, 6)
                        if existencias_item:
                            existencias_item.setText(str(existencias))
                        break
                else:
                    # Si el ID no existe en la tabla, agregar un nuevo registro
                    row_position = self.inventory_table.rowCount()
                    self.inventory_table.insertRow(row_position)
                    for col, data in enumerate(product):
                        item = QTableWidgetItem(str(data))
                        if col in [0, 5, 6]:
                            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.inventory_table.setItem(row_position, col, item)
                    existencias_item = QTableWidgetItem(str(existencias))
                    existencias_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.inventory_table.setItem(row_position, 6, existencias_item)

                # Limpiar la entrada del ID
                self.id_edit.clear()
                
                # Establecer el foco de nuevo en el campo de entrada de ID
                self.id_edit.setFocus()
            else:
                # El producto no se encontró en la base de datos
                QMessageBox.warning(self, "Producto no encontrado", f"No se encontró ningún producto con el ID {product_id}.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al agregar el producto: {str(e)}")


    def on_page_enter(self):
        # Limpiar la entrada del ID al entrar en la página
        self.id_edit.clear()




#--------------------------------------------------# MAIN CLASS #--------------------------------------------------#
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        # Crear una instancia de DatabaseManager
        self.database_manager = DatabaseManager(DATABASE_NAME)

        self.setWindowTitle("Mikel Inventory")

        self.setGeometry(100, 100, 800, 600)
        

        # Crear el widget central y el stack de páginas
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.stacked_widget = QStackedWidget(self.central_widget)
        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_layout.addWidget(self.stacked_widget)

        self.user_triggered_import = False  # Variable de bandera

        # Crear la barra de menú
        menubar = self.menuBar()
        # Menu Archivo
        file_menu = menubar.addMenu("Archivo")


        #import_data_action = QAction('Importar datos', self)
        #import_data_action.triggered.connect(self.import_data)
        #import_data_action.setShortcut('Ctrl+J')
        #file_menu.addAction(import_data_action)

        import_data_action = QAction('Importar datos', self)
        import_data_action.triggered.connect(self.trigger_import_data)  # Conectar a trigger_import_data
        import_data_action.setShortcut('Ctrl+M')
        file_menu.addAction(import_data_action)

        
        # En el método __init__ de la clase que contiene la página donde está el botón
        #import_data_button = QPushButton('Importar Datos', self)
        #import_data_button.clicked.connect(self.import_data)


        register_product_action = QAction("Registrar Producto", self)
        register_product_action.triggered.connect(self.show_register_product_page)
        register_product_action.setShortcut('Ctrl+R')
        file_menu.addAction(register_product_action)


        #export_data_action = QAction('Exportar datos', self)
        #export_data_action.triggered.connect(self.export_to_excel)
        #export_data_action.triggered.connect(self.export_to_excel)
        #file_menu.addAction(export_data_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Salir', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Menu Editar
        edit_menu = menubar.addMenu("Editar")
        
        #register_product_action = QAction("Registrar Producto", self)
        #register_product_action.triggered.connect(self.show_register_product_page)
        #register_product_action.setShortcut('Ctrl+R')
        #edit_menu.addAction(register_product_action)

        update_product_action = QAction("Actualizar Producto", self)
        update_product_action.triggered.connect(self.show_update_product_page)
        update_product_action.setShortcut('Ctrl+U')
        edit_menu.addAction(update_product_action)

        delete_product_action = QAction("Eliminar Producto", self)
        delete_product_action.triggered.connect(self.show_delete_product_page)
        delete_product_action.setShortcut('Ctrl+D')
        edit_menu.addAction(delete_product_action)

        # Menu Ver
        view_menu = menubar.addMenu("Ver")
        
        search_product_action = QAction("Buscar Producto", self)
        search_product_action.triggered.connect(self.show_search_product_page)
        search_product_action.setShortcut('Ctrl+B')
        view_menu.addAction(search_product_action)

        view_product_action = QAction("Lista de Productos", self)
        view_product_action.triggered.connect(self.show_view_product_page)
        view_product_action.setShortcut('Ctrl+L')
        view_menu.addAction(view_product_action)

        # Menu Herramientas
        tools_menu = menubar.addMenu("Herramientas")

        generate_qr_action = QAction("Generar QR", self)
        generate_qr_action.triggered.connect(self.show_generate_qr_page)
        generate_qr_action.setShortcut('Ctrl+T')
        tools_menu.addAction(generate_qr_action)

        inventory_product_action = QAction("Inventario", self)
        inventory_product_action.triggered.connect(self.show_inventory_product_page)
        inventory_product_action.setShortcut('Ctrl+I')
        tools_menu.addAction(inventory_product_action)

        help_menu = menubar.addMenu("Ayuda")
        
        show_documentation_action = QAction("Documentación", self)
        show_documentation_action.triggered.connect(self.show_documentation) #LLAMADA AL METODO
        show_documentation_action.setShortcut('Ctrl+H')
        help_menu.addAction(show_documentation_action)

        help_menu.addSeparator()

        show_about_action = QAction("Acerca", self)
        show_about_action.triggered.connect(self.show_about)
        help_menu.addAction(show_about_action)

        # Agregar las páginas al stacked widget
        self.home_page = HomePage(self)
        self.register_product_page = RegisterProductPage(self)
        self.update_product_page = UpdateProductPage(self)
        self.delete_product_page = DeleteProductPage(self)
        self.search_product_page = SearchProductPage(self)
        self.view_product_page = ViewProductPage(self)
        self.generate_qr_page = GenerateQRPage(self)
        self.inventory_product_page = InventoryProductPage(self)

        self.stacked_widget.addWidget(self.home_page)
        self.stacked_widget.addWidget(self.register_product_page)
        self.stacked_widget.addWidget(self.update_product_page)
        self.stacked_widget.addWidget(self.delete_product_page)
        self.stacked_widget.addWidget(self.search_product_page)
        self.stacked_widget.addWidget(self.view_product_page)
        self.stacked_widget.addWidget(self.generate_qr_page)
        self.stacked_widget.addWidget(self.inventory_product_page)

        # En el método __init__ de la clase que contiene la página donde está el botón
        #import_data_button = QPushButton('Importar Datos', self)
        #import_data_button.clicked.connect(self.import_data)

    def show_register_product_page(self):
        self.stacked_widget.setCurrentWidget(self.register_product_page)

    def show_update_product_page(self):
        self.stacked_widget.setCurrentWidget(self.update_product_page)

    def show_delete_product_page(self):
        self.stacked_widget.setCurrentWidget(self.delete_product_page)

    def show_search_product_page(self):
        self.stacked_widget.setCurrentWidget(self.search_product_page)
    
    def show_view_product_page(self):
        self.stacked_widget.setCurrentWidget(self.view_product_page)

    def show_generate_qr_page(self):
        self.stacked_widget.setCurrentWidget(self.generate_qr_page)

    def show_inventory_product_page(self):
        self.stacked_widget.setCurrentWidget(self.inventory_product_page)





    def verify_expiration_date(self):
        today_date = datetime.now()
        if today_date > expiration_date:
            logging.warning("Hay una nueva version disponible de la aplicación.")
            QMessageBox.critical(self, "Aplicación desactualizada", "Nueva versión disponible. Por favor, póngase en contacto con el soporte para obtener instrucciones sobre cómo actualizar la aplicación.")
            sys.exit(1)


    def verify_system_integrity(self):
        # Obtiene la fecha actual del sistema
        system_date = datetime.now()
        
        # Compara la fecha actual del sistema con la fecha de vencimiento
        if system_date < expiration_date:
            # La fecha del sistema es anterior a la fecha de vencimiento
            logging.info("La fecha del sistema es válida.")
        else:
            # La fecha del sistema es igual o posterior a la fecha de vencimiento
            logging.warning("La fecha del sistema ha sido modificada.")
            QMessageBox.critical(self, "Error", "La fecha del sistema ha sido modificada. Por favor, póngase en contacto con el soporte.")
            sys.exit(1)

    def show_documentation(self):
        #Obtiene la ruta absoluta del archivo de documentación dentro de la carpeta de la aplicación
        app_folder = os.path.dirname(os.path.abspath(__file__))
        documentation_filename = DOCUMENTATION  # Nombre del archivo de documentación
        documentation_path = os.path.join(app_folder, documentation_filename)

        if os.path.exists(documentation_path):
            try:
                # Usa el módulo 'webbrowser' para abrir el PDF en el navegador predeterminado
                webbrowser.open_new_tab(documentation_path)
            except Exception as e:
                QMessageBox.warning(self, "Error al abrir", f"No se pudo abrir el documento: {str(e)}")
        else:
            QMessageBox.warning(self, "Documento no encontrado", "El archivo de documentación no se encuentra en la ubicación especificada.")




    def show_about(self):
        
        about = QMessageBox(self)
        about.setWindowTitle('Acerca de Mikel Inventory')

        about.setWindowIcon(QIcon(os.path.join(basedir, "icons", "mikel.svg")))

        # Agregar un ícono a la izquierda del texto
        icon_pixmap = QPixmap(os.path.join(basedir, "icons", "info.svg"))
        about.setIconPixmap(icon_pixmap)

        about.setText(f'\n{__message__}\n\n{__copyright__} {__author__}\n\nStable Channel, Build {__version__}')
        about.exec()

    def import_data(self):
        if self.user_triggered_import:  # Verificar si la acción fue desencadenada por el usuario
            # Obtener la ruta del archivo CSV
            csv_file_path, _ = QFileDialog.getOpenFileName(self, 'Seleccionar archivo CSV', '', 'CSV Files (*.csv)')

            if csv_file_path:
                try:
                    # Llamar al método de importación en DatabaseManager
                    imported_count = self.database_manager.import_data_csv(csv_file_path)

                    # Mostrar un mensaje de éxito con la cantidad de registros importados
                    success_message = f'Los datos se importaron correctamente. Registros importados: {imported_count}'
                    QMessageBox.information(self, 'Importación exitosa', success_message)
                except Exception as e:
                    QMessageBox.critical(self, 'Error de importación', str(e))

            self.user_triggered_import = False  # Reinicia la variable de bandera

    def trigger_import_data(self):
        self.user_triggered_import = True
        self.import_data()


    def show_confirmation(self):
        respuesta = QMessageBox.question(
            self, 'Confirmación', '¿Estás seguro de que deseas cerrar la aplicación?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if respuesta == QMessageBox.Yes:
            self.close()

    def closeEvent(self, event):
        respuesta = QMessageBox.question(
            self, 'Confirmación', '¿Estás seguro de que deseas cerrar la aplicación?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

        if respuesta == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()


def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join(basedir, "icons", "mikel.svg")))
    #app.setStyle('Fusion')
    #app.setStyleSheet('Fusion')
    #app.setStyleSheet("QWidget { background-color: #ffffff; }")
    window = MainWindow()
    window.verify_expiration_date()
    window.verify_system_integrity()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()





