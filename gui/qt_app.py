#!/usr/bin/env python3
"""
SmartCityOS GUI - PySide6 (Qt)
Migração faseada da interface Tkinter para Qt.
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta
from random import choice

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QIcon, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QFileDialog,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import psycopg as psy
from psycopg import sql
from psycopg.rows import dict_row
from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)



def format_currency_brl(value):
    """Formata valor monetário para o padrão brasileiro (R$ 1.234,56)."""
    if value is None or value == 0:
        return "R$ 0,00"

    value = round(float(value), 2)
    integer_part = int(value)
    decimal_part = int(round((value - integer_part) * 100))

    if integer_part >= 1000:
        integer_formatted = f"{integer_part:,}".replace(",", ".")
    else:
        integer_formatted = str(integer_part)

    return f"R$ {integer_formatted},{decimal_part:02d}"


def parse_money_input(value):
    """Converte entrada monetária brasileira para float."""
    if value is None:
        return 0.0
    text = str(value).replace("R$", "").strip()
    if not text:
        return 0.0
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    else:
        text = text.replace(",", ".")
    return float(text)


class StatCard(QFrame):
    """Card de estatística usado no Dashboard."""

    def __init__(self, title, total, secondary, extra, color, parent=None):
        super().__init__(parent)
        self.setProperty("role", "card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame(self)
        header.setProperty("role", "card_header")
        header.setStyleSheet(f"background: {color};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 10, 8, 10)

        title_label = QLabel(title, header)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #FFFFFF; font-weight: 600;")
        header_layout.addWidget(title_label)

        body = QWidget(self)
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(16, 14, 16, 14)
        body_layout.setSpacing(6)

        total_label = QLabel(str(total), body)
        total_label.setStyleSheet(
            f"color: {color}; font-size: 28px; font-weight: 700;"
        )

        secondary_label = QLabel(secondary, body)
        secondary_label.setStyleSheet("color: #696969;")

        extra_label = QLabel(extra, body)
        extra_label.setStyleSheet("color: #2F4F4F; font-size: 11px;")

        body_layout.addWidget(total_label)
        body_layout.addWidget(secondary_label)
        body_layout.addWidget(extra_label)
        body_layout.addStretch(1)

        layout.addWidget(header)
        layout.addWidget(body)


class PlaceholderPage(QWidget):
    """Página placeholder para telas ainda não migradas."""

    def __init__(self, title, description, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        title_label = QLabel(title, self)
        title_label.setStyleSheet("font-size: 20px; font-weight: 700;")

        desc_label = QLabel(description, self)
        desc_label.setStyleSheet("color: #696969; font-size: 12px;")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(desc_label)


class DashboardPage(QWidget):
    """Página do Dashboard com cards de estatísticas."""

    def __init__(self, refresh_callback, parent=None):
        super().__init__(parent)
        self.refresh_callback = refresh_callback

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QFrame(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)

        self.title_label = QLabel("📊 Dashboard - Visão Geral", header)
        self.title_label.setStyleSheet("font-size: 16px; font-weight: 700;")

        self.refresh_button = QPushButton("🔄 Atualizar", header)
        self.refresh_button.setObjectName("SuccessButton")
        self.refresh_button.clicked.connect(self.refresh_callback)

        header_layout.addWidget(self.title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.refresh_button)

        self.message_label = QLabel(
            "Conecte-se ao banco de dados para visualizar estatísticas.",
            self,
        )
        self.message_label.setStyleSheet("color: #696969; font-size: 12px;")
        self.message_label.setAlignment(Qt.AlignCenter)

        self.cards_container = QWidget(self)
        self.cards_layout = QGridLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setHorizontalSpacing(12)
        self.cards_layout.setVerticalSpacing(12)

        layout.addWidget(header)
        layout.addWidget(self.message_label)
        layout.addWidget(self.cards_container)
        layout.addStretch(1)

        self.set_connected(False)

    def set_connected(self, connected):
        self.message_label.setVisible(not connected)
        self.cards_container.setVisible(connected)

    def update_cards(self, cards_data):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for i, (title, total, secondary, extra, color) in enumerate(cards_data):
            row = i // 3
            col = i % 3
            card = StatCard(title, total, secondary, extra, color, self.cards_container)
            self.cards_layout.addWidget(card, row, col)


class SummaryCard(QFrame):
    """Card compacto para estatísticas de listagens."""

    def __init__(self, title, value, extra, color, parent=None):
        super().__init__(parent)
        self.setProperty("role", "summary_card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame(self)
        header.setStyleSheet(f"background: {color};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 8, 8, 8)

        title_label = QLabel(title, header)
        title_label.setStyleSheet("color: #FFFFFF; font-weight: 600;")
        header_layout.addWidget(title_label)

        body = QWidget(self)
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(12, 10, 12, 10)
        body_layout.setSpacing(4)

        self.value_label = QLabel(str(value), body)
        self.value_label.setStyleSheet(
            f"color: {color}; font-size: 20px; font-weight: 700;"
        )

        self.extra_label = QLabel(extra, body)
        self.extra_label.setStyleSheet("color: #696969; font-size: 11px;")

        body_layout.addWidget(self.value_label)
        body_layout.addWidget(self.extra_label)

        layout.addWidget(header)
        layout.addWidget(body)

    def update(self, value, extra):
        self.value_label.setText(str(value))
        self.extra_label.setText(extra)


class AddCitizenDialog(QDialog):
    """Diálogo para adicionar cidadão."""

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.colors = app.colors
        self.fonts = app.fonts

        self.setWindowTitle("➕ Adicionar Cidadão")
        self.resize(720, 760)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QFrame(self)
        header.setStyleSheet(f"background: {self.colors['primary']}; border-radius: 6px;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)

        title = QLabel("👤 Novo Cidadão", header)
        title.setStyleSheet(f"color: {self.colors['white']}; font-size: 16px; font-weight: 700;")
        header_layout.addWidget(title)
        layout.addWidget(header)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)

        content = QWidget(scroll_area)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        self.fields = {}

        personal_group = QGroupBox("👤 Dados Pessoais", content)
        personal_layout = QFormLayout(personal_group)
        personal_layout.setLabelAlignment(Qt.AlignLeft)

        self.fields["username"] = QLineEdit(personal_group)
        self.fields["username"].setPlaceholderText("Digite o nome de usuário")
        personal_layout.addRow("🔐 Nome de Usuário", self.fields["username"])

        self.fields["password"] = QLineEdit(personal_group)
        self.fields["password"].setEchoMode(QLineEdit.Password)
        self.fields["password"].setPlaceholderText("Digite a senha")
        personal_layout.addRow("🔒 Senha", self.fields["password"])

        self.fields["first_name"] = QLineEdit(personal_group)
        self.fields["first_name"].setPlaceholderText("Digite o nome")
        personal_layout.addRow("👤 Nome", self.fields["first_name"])

        self.fields["last_name"] = QLineEdit(personal_group)
        self.fields["last_name"].setPlaceholderText("Digite o sobrenome")
        personal_layout.addRow("👥 Sobrenome", self.fields["last_name"])

        self.fields["cpf"] = QLineEdit(personal_group)
        self.fields["cpf"].setPlaceholderText("Digite o CPF (11 dígitos)")
        personal_layout.addRow("📋 CPF", self.fields["cpf"])

        self.fields["birth_date"] = QLineEdit(personal_group)
        self.fields["birth_date"].setPlaceholderText("DD/MM/AAAA")
        personal_layout.addRow("🎂 Data de Nascimento", self.fields["birth_date"])

        content_layout.addWidget(personal_group)

        contact_group = QGroupBox("📞 Contato", content)
        contact_layout = QFormLayout(contact_group)
        contact_layout.setLabelAlignment(Qt.AlignLeft)

        self.fields["email"] = QLineEdit(contact_group)
        self.fields["email"].setPlaceholderText("Digite o email")
        contact_layout.addRow("📧 Email", self.fields["email"])

        self.fields["phone"] = QLineEdit(contact_group)
        self.fields["phone"].setPlaceholderText("Digite o telefone")
        contact_layout.addRow("📱 Telefone", self.fields["phone"])

        content_layout.addWidget(contact_group)

        address_group = QGroupBox("🏠 Endereço", content)
        address_layout = QFormLayout(address_group)
        address_layout.setLabelAlignment(Qt.AlignLeft)

        self.fields["state"] = QLineEdit(address_group)
        self.fields["state"].setPlaceholderText("UF")
        address_layout.addRow("🏠 Estado", self.fields["state"])

        self.fields["city"] = QLineEdit(address_group)
        self.fields["city"].setPlaceholderText("Cidade")
        address_layout.addRow("🏙️ Cidade", self.fields["city"])

        self.fields["neighborhood"] = QLineEdit(address_group)
        self.fields["neighborhood"].setPlaceholderText("Bairro")
        address_layout.addRow("🏘️ Bairro", self.fields["neighborhood"])

        self.fields["street"] = QLineEdit(address_group)
        self.fields["street"].setPlaceholderText("Rua")
        address_layout.addRow("🛣️ Rua", self.fields["street"])

        self.fields["number"] = QLineEdit(address_group)
        self.fields["number"].setPlaceholderText("Número")
        address_layout.addRow("🔢 Número", self.fields["number"])

        self.fields["complement"] = QLineEdit(address_group)
        self.fields["complement"].setPlaceholderText("Complemento")
        address_layout.addRow("📝 Complemento", self.fields["complement"])

        content_layout.addWidget(address_group)

        financial_group = QGroupBox("💰 Financeiro", content)
        financial_layout = QFormLayout(financial_group)
        financial_layout.setLabelAlignment(Qt.AlignLeft)

        self.fields["wallet_balance"] = QLineEdit(financial_group)
        self.fields["wallet_balance"].setText("0.00")
        self.fields["wallet_balance"].setPlaceholderText("0.00")
        financial_layout.addRow("💰 Saldo Inicial (R$)", self.fields["wallet_balance"])

        content_layout.addWidget(financial_group)
        content_layout.addStretch(1)

        scroll_area.setWidget(content)
        layout.addWidget(scroll_area)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)

        cancel_btn = QPushButton("❌ Cancelar", self)
        cancel_btn.setObjectName("DangerButton")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("💾 Salvar", self)
        save_btn.setObjectName("SuccessButton")
        save_btn.clicked.connect(self.save_citizen)

        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(save_btn)

        layout.addLayout(buttons_layout)

    def save_citizen(self):
        try:
            username = self.fields["username"].text().strip()
            password = self.fields["password"].text().strip()
            first_name = self.fields["first_name"].text().strip()
            last_name = self.fields["last_name"].text().strip()
            cpf = self.fields["cpf"].text().strip()
            birth_date = self.fields["birth_date"].text().strip()
            email = self.fields["email"].text().strip()
            phone = self.fields["phone"].text().strip()
            state = self.fields["state"].text().strip()
            city = self.fields["city"].text().strip()
            neighborhood = self.fields["neighborhood"].text().strip()
            street = self.fields["street"].text().strip()
            number = self.fields["number"].text().strip()
            complement = self.fields["complement"].text().strip()

            if not all([username, password, first_name, last_name, cpf, email, state, city, street]):
                QMessageBox.warning(self, "Erro", "Preencha todos os campos obrigatórios!")
                return

            cpf_clean = cpf.replace(".", "").replace("-", "")
            if len(cpf_clean) != 11 or not cpf_clean.isdigit():
                QMessageBox.warning(self, "Erro", "CPF inválido! Deve ter 11 dígitos.")
                return

            try:
                birth_date_obj = datetime.strptime(birth_date, "%d/%m/%Y").date()
            except Exception:
                QMessageBox.warning(
                    self,
                    "Erro",
                    "Data de nascimento inválida! Use DD/MM/AAAA",
                )
                return

            if not self.app.is_username_available(username):
                QMessageBox.warning(
                    self,
                    "Erro",
                    f"Username '{username}' já está em uso! Escolha outro.",
                )
                return

            address_parts = [street, number, neighborhood, city, state]
            if complement:
                address_parts.append(complement)
            address = ", ".join(address_parts)

            wallet_balance = parse_money_input(self.fields["wallet_balance"].text())

            conn_string = self.app.get_connection_string()
            with psy.connect(conn_string) as conn:
                with conn.cursor() as cur:
                    password_hash = password

                    cur.execute(
                        """
                        INSERT INTO app_user (username, password_hash)
                        VALUES (%s, %s) RETURNING id
                        """,
                        (username, password_hash),
                    )
                    app_user_id = cur.fetchone()[0]

                    cur.execute(
                        """
                        INSERT INTO citizen (
                            app_user_id, first_name, last_name, cpf, birth_date,
                            email, phone, address, wallet_balance
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            app_user_id,
                            first_name,
                            last_name,
                            cpf_clean,
                            birth_date_obj,
                            email,
                            phone,
                            address,
                            wallet_balance,
                        ),
                    )
                conn.commit()

            QMessageBox.information(self, "Sucesso", "Cidadão adicionado com sucesso!")
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao adicionar cidadão: {exc}")


class AddVehicleDialog(QDialog):
    """Diálogo para adicionar veículo."""

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.colors = app.colors

        self.setWindowTitle("➕ Adicionar Veículo")
        self.resize(520, 420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QFrame(self)
        header.setStyleSheet(f"background: {self.colors['warning']}; border-radius: 6px;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)

        title = QLabel("🚗 Novo Veículo", header)
        title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 700;")
        header_layout.addWidget(title)
        layout.addWidget(header)

        form_widget = QWidget(self)
        form_layout = QFormLayout(form_widget)
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignTop)

        self.fields = {}

        self.fields["username"] = QLineEdit(form_widget)
        self.fields["username"].setPlaceholderText("Digite o nome de usuário para o veículo")
        form_layout.addRow("🔐 Nome de Usuário", self.fields["username"])

        self.fields["password"] = QLineEdit(form_widget)
        self.fields["password"].setEchoMode(QLineEdit.Password)
        self.fields["password"].setPlaceholderText("Digite a senha")
        form_layout.addRow("🔒 Senha", self.fields["password"])

        self.fields["license_plate"] = QLineEdit(form_widget)
        self.fields["license_plate"].setPlaceholderText("ABC-1234")
        form_layout.addRow("🚗 Placa", self.fields["license_plate"])

        self.fields["model"] = QLineEdit(form_widget)
        self.fields["model"].setPlaceholderText("Ex: Fiat Palio")
        form_layout.addRow("📋 Modelo", self.fields["model"])

        self.fields["year"] = QLineEdit(form_widget)
        self.fields["year"].setPlaceholderText("2024")
        form_layout.addRow("📅 Ano", self.fields["year"])

        self.fields["citizen_cpf"] = QLineEdit(form_widget)
        self.fields["citizen_cpf"].setPlaceholderText("CPF do cidadão proprietário (opcional)")
        form_layout.addRow("👤 CPF do Proprietário", self.fields["citizen_cpf"])

        layout.addWidget(form_widget)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)

        cancel_btn = QPushButton("❌ Cancelar", self)
        cancel_btn.setObjectName("DangerButton")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("💾 Salvar", self)
        save_btn.setObjectName("SuccessButton")
        save_btn.clicked.connect(self.save_vehicle)

        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(save_btn)
        layout.addLayout(buttons_layout)

    def save_vehicle(self):
        try:
            username = self.fields["username"].text().strip()
            password = self.fields["password"].text().strip()
            license_plate = self.fields["license_plate"].text().strip().upper()
            model = self.fields["model"].text().strip()
            year_text = self.fields["year"].text().strip()
            citizen_cpf = self.fields["citizen_cpf"].text().strip()

            if not all([username, password, license_plate, model, year_text]):
                QMessageBox.warning(self, "Erro", "Preencha todos os campos obrigatórios!")
                return

            try:
                year = int(year_text)
                current_year = datetime.now().year
                if year < 1900 or year > current_year + 1:
                    QMessageBox.warning(
                        self,
                        "Erro",
                        f"Ano inválido! Deve estar entre 1900 e {current_year + 1}",
                    )
                    return
            except ValueError:
                QMessageBox.warning(self, "Erro", "Ano deve ser um número válido!")
                return

            if len(license_plate) < 7:
                QMessageBox.warning(
                    self,
                    "Erro",
                    "Placa muito curta! Mínimo 7 caracteres.",
                )
                return

            citizen_id = None
            if citizen_cpf:
                cpf_clean = citizen_cpf.replace(".", "").replace("-", "")
                if len(cpf_clean) != 11 or not cpf_clean.isdigit():
                    QMessageBox.warning(self, "Erro", "CPF inválido! Deve ter 11 dígitos.")
                    return

                conn_string = self.app.get_connection_string()
                with psy.connect(conn_string) as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT id FROM citizen_active WHERE cpf = %s",
                            (cpf_clean,),
                        )
                        citizen_result = cur.fetchone()
                        if citizen_result:
                            citizen_id = citizen_result[0]
                        else:
                            QMessageBox.warning(
                                self,
                                "Erro",
                                "CPF não encontrado no sistema! Cadastre o cidadão primeiro.",
                            )
                            return

            if not self.app.is_username_available(username):
                QMessageBox.warning(
                    self,
                    "Erro",
                    f"Username '{username}' já está em uso! Escolha outro.",
                )
                return

            conn_string = self.app.get_connection_string()
            with psy.connect(conn_string) as conn:
                with conn.cursor() as cur:
                    password_hash = password

                    cur.execute(
                        """
                        INSERT INTO app_user (username, password_hash)
                        VALUES (%s, %s) RETURNING id
                        """,
                        (username, password_hash),
                    )
                    app_user_id = cur.fetchone()[0]

                    cur.execute(
                        """
                        INSERT INTO vehicle (
                            app_user_id, license_plate, model, year, citizen_id
                        ) VALUES (%s, %s, %s, %s, %s) RETURNING id
                        """,
                        (app_user_id, license_plate, model, year, citizen_id),
                    )
                    vehicle_id = cur.fetchone()[0]

                    if citizen_id:
                        cur.execute(
                            """
                            INSERT INTO vehicle_citizen (vehicle_id, citizen_id)
                            VALUES (%s, %s)
                            """,
                            (vehicle_id, citizen_id),
                        )
                conn.commit()

            QMessageBox.information(self, "Sucesso", "Veículo adicionado com sucesso!")
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao adicionar veículo: {exc}")


class AddSensorDialog(QDialog):
    """Diálogo para adicionar sensor."""

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.colors = app.colors

        self.setWindowTitle("➕ Adicionar Sensor")
        self.resize(520, 420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QFrame(self)
        header.setStyleSheet(f"background: {self.colors['dark']}; border-radius: 6px;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)

        title = QLabel("📹 Novo Sensor", header)
        title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 700;")
        header_layout.addWidget(title)
        layout.addWidget(header)

        form_widget = QWidget(self)
        form_layout = QFormLayout(form_widget)
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignTop)

        self.fields = {}

        self.fields["username"] = QLineEdit(form_widget)
        self.fields["username"].setPlaceholderText("Digite o nome de usuário para o sensor")
        form_layout.addRow("🔐 Nome de Usuário", self.fields["username"])

        self.fields["password"] = QLineEdit(form_widget)
        self.fields["password"].setEchoMode(QLineEdit.Password)
        self.fields["password"].setPlaceholderText("Digite a senha")
        form_layout.addRow("🔒 Senha", self.fields["password"])

        self.fields["model"] = QLineEdit(form_widget)
        self.fields["model"].setPlaceholderText("Ex: IP Camera X100")
        form_layout.addRow("📋 Modelo", self.fields["model"])

        self.fields["type"] = QComboBox(form_widget)
        self.fields["type"].addItems(
            [
                "Câmera",
                "Radar",
                "LIDAR",
                "Sensor de Tráfego",
                "Sensor de Velocidade",
                "Outro",
            ]
        )
        form_layout.addRow("📹 Tipo", self.fields["type"])

        self.fields["location"] = QLineEdit(form_widget)
        self.fields["location"].setPlaceholderText("Ex: Av. Principal, 1000")
        form_layout.addRow("📍 Localização", self.fields["location"])

        layout.addWidget(form_widget)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)

        cancel_btn = QPushButton("❌ Cancelar", self)
        cancel_btn.setObjectName("DangerButton")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("💾 Salvar", self)
        save_btn.setObjectName("SuccessButton")
        save_btn.clicked.connect(self.save_sensor)

        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(save_btn)
        layout.addLayout(buttons_layout)

    def save_sensor(self):
        try:
            username = self.fields["username"].text().strip()
            password = self.fields["password"].text().strip()
            model = self.fields["model"].text().strip()
            sensor_type = self.fields["type"].currentText().strip()
            location = self.fields["location"].text().strip()

            if not all([username, password, model, sensor_type, location]):
                QMessageBox.warning(self, "Erro", "Preencha todos os campos obrigatórios!")
                return

            if not self.app.is_username_available(username):
                QMessageBox.warning(
                    self,
                    "Erro",
                    f"Username '{username}' já está em uso! Escolha outro.",
                )
                return

            conn_string = self.app.get_connection_string()
            with psy.connect(conn_string) as conn:
                with conn.cursor() as cur:
                    password_hash = password

                    cur.execute(
                        """
                        INSERT INTO app_user (username, password_hash)
                        VALUES (%s, %s) RETURNING id
                        """,
                        (username, password_hash),
                    )
                    app_user_id = cur.fetchone()[0]

                    cur.execute(
                        """
                        INSERT INTO sensor (
                            app_user_id, model, type, location
                        ) VALUES (%s, %s, %s, %s)
                        """,
                        (app_user_id, model, sensor_type, location),
                    )
                conn.commit()

            QMessageBox.information(self, "Sucesso", "Sensor adicionado com sucesso!")
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao adicionar sensor: {exc}")


class AddIncidentDialog(QDialog):
    """Diálogo para registrar incidente."""

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.colors = app.colors

        self.setWindowTitle("➕ Registrar Incidente")
        self.resize(560, 460)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QFrame(self)
        header.setStyleSheet(f"background: {self.colors['accent']}; border-radius: 6px;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)

        title = QLabel("⚠️ Novo Incidente", header)
        title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 700;")
        header_layout.addWidget(title)
        layout.addWidget(header)

        form_widget = QWidget(self)
        form_layout = QFormLayout(form_widget)
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignTop)

        self.vehicle_combo = QComboBox(form_widget)
        self.sensor_combo = QComboBox(form_widget)
        self.location_input = QLineEdit(form_widget)
        self.location_input.setPlaceholderText("Ex: Av. Principal, esquina com Rua Secundária")

        self.description_input = QTextEdit(form_widget)
        self.description_input.setPlaceholderText("Descreva o incidente em detalhes")
        self.description_input.setFixedHeight(110)

        self.vehicle_combo.addItem("Selecione o veículo")
        self.sensor_combo.addItem("Selecione o sensor")

        self._load_dropdowns()

        form_layout.addRow("🚗 Veículo", self.vehicle_combo)
        form_layout.addRow("📹 Sensor", self.sensor_combo)
        form_layout.addRow("📍 Localização", self.location_input)
        form_layout.addRow("📝 Descrição", self.description_input)

        layout.addWidget(form_widget)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)

        cancel_btn = QPushButton("❌ Cancelar", self)
        cancel_btn.setObjectName("DangerButton")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("💾 Salvar", self)
        save_btn.setObjectName("SuccessButton")
        save_btn.clicked.connect(self.save_incident)

        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(save_btn)
        layout.addLayout(buttons_layout)

    def _load_dropdowns(self):
        try:
            conn_string = self.app.get_connection_string()
            with psy.connect(conn_string) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT license_plate, model
                        FROM vehicle_active
                        WHERE allowed = true
                        ORDER BY license_plate
                        """
                    )
                    for plate, model in cur.fetchall():
                        self.vehicle_combo.addItem(f"{plate} - {model}")

                    cur.execute(
                        """
                        SELECT id, location, type
                        FROM sensor_active
                        WHERE active = true
                        ORDER BY location
                        """
                    )
                    for sensor_id, location, sensor_type in cur.fetchall():
                        self.sensor_combo.addItem(f"{sensor_id} - {sensor_type} - {location}")
        except Exception:
            pass

    def save_incident(self):
        try:
            vehicle_text = self.vehicle_combo.currentText()
            sensor_text = self.sensor_combo.currentText()
            location = self.location_input.text().strip()
            description = self.description_input.toPlainText().strip()

            if vehicle_text.startswith("Selecione") or sensor_text.startswith("Selecione"):
                QMessageBox.warning(self, "Erro", "Selecione o veículo e o sensor!")
                return

            if not location:
                QMessageBox.warning(self, "Erro", "Preencha a localização!")
                return

            if not description:
                QMessageBox.warning(self, "Erro", "Preencha a descrição do incidente!")
                return

            vehicle_plate = vehicle_text.split(" - ")[0]
            sensor_id = int(sensor_text.split(" - ")[0])

            conn_string = self.app.get_connection_string()
            with psy.connect(conn_string) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id FROM vehicle_active WHERE license_plate = %s",
                        (vehicle_plate,),
                    )
                    vehicle_result = cur.fetchone()
                    if not vehicle_result:
                        QMessageBox.warning(self, "Erro", "Veículo não encontrado!")
                        return
                    vehicle_id = vehicle_result[0]

                    cur.execute(
                        """
                        INSERT INTO traffic_incident (
                            vehicle_id, sensor_id, location, description
                        ) VALUES (%s, %s, %s, %s)
                        """,
                        (vehicle_id, sensor_id, location, description),
                    )
                conn.commit()

            QMessageBox.information(self, "Sucesso", "Incidente registrado com sucesso!")
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao registrar incidente: {exc}")


class PayFineDialog(QDialog):
    """Diálogo para pagar multa pendente."""

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.colors = app.colors
        self.fines_data = {}

        self.setWindowTitle("💳 Pagar Multa")
        self.resize(560, 420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QFrame(self)
        header.setStyleSheet(f"background: {self.colors['success']}; border-radius: 6px;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)

        title = QLabel("💳 Pagar Multa", header)
        title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 700;")
        header_layout.addWidget(title)
        layout.addWidget(header)

        form_widget = QWidget(self)
        form_layout = QFormLayout(form_widget)
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignTop)

        self.fine_combo = QComboBox(form_widget)
        self.amount_input = QLineEdit(form_widget)
        self.amount_input.setReadOnly(True)

        self.payment_method = QComboBox(form_widget)
        self.payment_method.addItems(
            [
                "Carteira Digital",
                "Cartão de Crédito",
                "Cartão de Débito",
                "Dinheiro",
                "PIX",
                "Boleto",
                "Transferência Bancária",
            ]
        )

        self._load_fines()

        self.fine_combo.currentIndexChanged.connect(self._update_amount)

        form_layout.addRow("💰 Multa Pendente", self.fine_combo)
        form_layout.addRow("💳 Valor a Pagar (R$)", self.amount_input)
        form_layout.addRow("🏦 Método de Pagamento", self.payment_method)

        layout.addWidget(form_widget)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)

        cancel_btn = QPushButton("❌ Cancelar", self)
        cancel_btn.setObjectName("DangerButton")
        cancel_btn.clicked.connect(self.reject)

        pay_btn = QPushButton("💳 Pagar", self)
        pay_btn.setObjectName("SuccessButton")
        pay_btn.clicked.connect(self.pay_fine)

        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(pay_btn)
        layout.addLayout(buttons_layout)

    def _load_fines(self):
        self.fine_combo.clear()
        self.fines_data = {}
        self.fine_combo.addItem("Selecione uma multa")

        try:
            conn_string = self.app.get_connection_string()
            with psy.connect(conn_string) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        """
                        SELECT f.id, f.amount, f.due_date, f.created_at,
                               ti.location, ti.occurred_at,
                               v.license_plate, c.first_name, c.last_name
                        FROM fine f
                        JOIN traffic_incident ti ON f.traffic_incident_id = ti.id
                        LEFT JOIN vehicle v ON ti.vehicle_id = v.id
                        LEFT JOIN citizen c ON v.citizen_id = c.id
                        WHERE f.status = 'pending'
                        ORDER BY f.due_date ASC
                        """
                    )
                    fines = cur.fetchall()

            for fine in fines:
                display = (
                    f"#{fine['id']} - {format_currency_brl(fine['amount'])} - "
                    f"Venc: {fine['due_date'].strftime('%d/%m/%Y')} - "
                    f"{fine.get('license_plate') or 'Veículo não identificado'}"
                )
                self.fines_data[display] = fine
                self.fine_combo.addItem(display)

        except Exception:
            pass

    def _update_amount(self):
        text = self.fine_combo.currentText()
        fine = self.fines_data.get(text)
        if fine:
            self.amount_input.setText(format_currency_brl(fine["amount"]).replace("R$ ", ""))
        else:
            self.amount_input.setText("")

    def pay_fine(self):
        try:
            fine_text = self.fine_combo.currentText()
            fine = self.fines_data.get(fine_text)
            if not fine:
                QMessageBox.warning(self, "Erro", "Selecione uma multa!")
                return

            payment_method = self.payment_method.currentText().strip()
            if not payment_method:
                QMessageBox.warning(self, "Erro", "Selecione o método de pagamento!")
                return

            fine_id = fine["id"]
            amount_paid = parse_money_input(self.amount_input.text())

            conn_string = self.app.get_connection_string()
            with psy.connect(conn_string) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT status, amount FROM fine WHERE id = %s", (fine_id,))
                    fine_result = cur.fetchone()
                    if not fine_result:
                        QMessageBox.warning(self, "Erro", "Multa não encontrada!")
                        return

                    status, db_amount = fine_result
                    if status != "pending":
                        QMessageBox.warning(self, "Erro", f"Esta multa já está {status}!")
                        return

                    amount_db = parse_money_input(db_amount)
                    if abs(amount_paid - amount_db) > 0.01:
                        QMessageBox.warning(self, "Erro", "Valor da multa não confere!")
                        return

                    cur.execute(
                        """
                        INSERT INTO fine_payment (
                            fine_id, amount_paid, payment_method
                        ) VALUES (%s, %s, %s)
                        """,
                        (fine_id, amount_paid, payment_method),
                    )
                conn.commit()

            QMessageBox.information(self, "Sucesso", "Multa paga com sucesso!")
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao pagar multa: {exc}")


class GenerateFineDialog(QDialog):
    """Diálogo para gerar multa."""

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.colors = app.colors
        self.incidents_data = {}

        self.setWindowTitle("💰 Gerar Multa")
        self.resize(560, 440)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QFrame(self)
        header.setStyleSheet(f"background: {self.colors['secondary']}; border-radius: 6px;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)

        title = QLabel("💰 Gerar Nova Multa", header)
        title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 700;")
        header_layout.addWidget(title)
        layout.addWidget(header)

        form_widget = QWidget(self)
        form_layout = QFormLayout(form_widget)
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignTop)

        self.incident_combo = QComboBox(form_widget)
        self.amount_input = QLineEdit(form_widget)
        self.amount_input.setPlaceholderText("150.00")
        self.due_date_input = QLineEdit(form_widget)
        self.due_date_input.setPlaceholderText("DD/MM/AAAA")

        self._load_incidents()

        form_layout.addRow("⚠️ Incidente", self.incident_combo)
        form_layout.addRow("💰 Valor (R$)", self.amount_input)
        form_layout.addRow("📅 Data Vencimento", self.due_date_input)

        layout.addWidget(form_widget)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)

        cancel_btn = QPushButton("❌ Cancelar", self)
        cancel_btn.setObjectName("DangerButton")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("💾 Gerar Multa", self)
        save_btn.setObjectName("SuccessButton")
        save_btn.clicked.connect(self.save_fine)

        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(save_btn)
        layout.addLayout(buttons_layout)

    def _load_incidents(self):
        self.incident_combo.clear()
        self.incidents_data = {}
        self.incident_combo.addItem("Selecione um incidente")

        try:
            conn_string = self.app.get_connection_string()
            with psy.connect(conn_string) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        """
                        SELECT ti.id, ti.location, ti.occurred_at, ti.description,
                               v.license_plate, c.first_name, c.last_name
                        FROM traffic_incident ti
                        LEFT JOIN vehicle v ON ti.vehicle_id = v.id
                        LEFT JOIN citizen c ON v.citizen_id = c.id
                        LEFT JOIN fine f ON ti.id = f.traffic_incident_id
                        WHERE f.id IS NULL
                        ORDER BY ti.occurred_at DESC
                        """
                    )
                    incidents = cur.fetchall()

            for inc in incidents:
                display_text = (
                    f"#{inc['id']} - {inc.get('license_plate') or 'Veículo não identificado'} - "
                    f"{inc.get('location') or 'Local não informado'} - "
                    f"{inc['occurred_at'].strftime('%d/%m %H:%M')}"
                )
                self.incidents_data[display_text] = inc
                self.incident_combo.addItem(display_text)
        except Exception:
            pass

    def save_fine(self):
        try:
            incident_text = self.incident_combo.currentText()
            incident = self.incidents_data.get(incident_text)
            if not incident:
                QMessageBox.warning(self, "Erro", "Selecione um incidente!")
                return

            amount_text = self.amount_input.text().strip()
            if not amount_text:
                QMessageBox.warning(self, "Erro", "Preencha o valor da multa!")
                return

            amount = parse_money_input(amount_text)
            if amount <= 0:
                QMessageBox.warning(self, "Erro", "Valor deve ser maior que zero!")
                return

            due_date_text = self.due_date_input.text().strip()
            try:
                due_date = datetime.strptime(due_date_text, "%d/%m/%Y").date()
            except ValueError:
                QMessageBox.warning(
                    self,
                    "Erro",
                    "Data de vencimento inválida! Use o formato DD/MM/AAAA",
                )
                return

            incident_id = incident["id"]
            incident_date = incident["occurred_at"].date() if incident.get("occurred_at") else None
            today = datetime.now().date()

            if incident_date and due_date < incident_date:
                QMessageBox.warning(
                    self,
                    "Erro",
                    "A data de vencimento não pode ser anterior à data do incidente!",
                )
                return

            if due_date < today - timedelta(days=365):
                QMessageBox.warning(
                    self,
                    "Erro",
                    "A data de vencimento não pode ser mais de 1 ano no passado!",
                )
                return

            conn_string = self.app.get_connection_string()
            with psy.connect(conn_string) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id FROM fine WHERE traffic_incident_id = %s",
                        (incident_id,),
                    )
                    if cur.fetchone():
                        QMessageBox.warning(
                            self, "Erro", "Este incidente já possui uma multa!"
                        )
                        return

                    cur.execute(
                        """
                        SELECT c.id as citizen_id
                        FROM traffic_incident ti
                        JOIN vehicle v ON v.id = ti.vehicle_id
                        JOIN citizen c ON c.id = v.citizen_id
                        WHERE ti.id = %s
                        """,
                        (incident_id,),
                    )
                    citizen_result = cur.fetchone()
                    if not citizen_result:
                        QMessageBox.warning(
                            self,
                            "Erro",
                            "Não foi possível encontrar o cidadão associado ao incidente!",
                        )
                        return
                    citizen_id = citizen_result[0]

                    cur.execute(
                        """
                        INSERT INTO fine (
                            traffic_incident_id, citizen_id, amount, due_date
                        ) VALUES (%s, %s, %s, %s)
                        """,
                        (incident_id, citizen_id, amount, due_date),
                    )
                conn.commit()

            QMessageBox.information(self, "Sucesso", "Multa gerada com sucesso!")
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar multa: {exc}")


class CitizensPage(QWidget):
    """Página de Gestão de Cidadãos."""

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.colors = app.colors
        self.fonts = app.fonts
        self.all_citizens = []
        self.filtered_citizens = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QFrame(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(12)

        title_label = QLabel("👥 Gestão de Cidadãos", header)
        title_label.setStyleSheet("font-size: 16px; font-weight: 700;")

        filters_widget = QWidget(header)
        filters_layout = QHBoxLayout(filters_widget)
        filters_layout.setContentsMargins(0, 0, 0, 0)
        filters_layout.setSpacing(8)

        self.name_filter = QLineEdit(filters_widget)
        self.name_filter.setPlaceholderText("Nome")
        self.name_filter.textChanged.connect(self.apply_filters)

        self.cpf_filter = QLineEdit(filters_widget)
        self.cpf_filter.setPlaceholderText("CPF")
        self.cpf_filter.textChanged.connect(self.apply_filters)

        self.status_filter = QComboBox(filters_widget)
        self.status_filter.addItems(["Todos", "Ativos", "Inativos"])
        self.status_filter.currentIndexChanged.connect(self.apply_filters)

        self.debt_filter = QComboBox(filters_widget)
        self.debt_filter.addItems(["Todos", "Com Dívida", "Sem Dívida"])
        self.debt_filter.currentIndexChanged.connect(self.apply_filters)

        self.add_button = QPushButton("➕ Adicionar", filters_widget)
        self.add_button.setObjectName("SuccessButton")
        self.add_button.clicked.connect(self.open_add_dialog)

        self.refresh_button = QPushButton("🔄 Atualizar", filters_widget)
        self.refresh_button.setObjectName("PrimaryButton")
        self.refresh_button.clicked.connect(self.load_citizens)

        self.delete_button = QPushButton("❌ Excluir", filters_widget)
        self.delete_button.setObjectName("DangerButton")
        self.delete_button.clicked.connect(self.delete_selected)

        filters_layout.addWidget(QLabel("🔍 Nome:", filters_widget))
        filters_layout.addWidget(self.name_filter)
        filters_layout.addWidget(QLabel("📋 CPF:", filters_widget))
        filters_layout.addWidget(self.cpf_filter)
        filters_layout.addWidget(QLabel("Status:", filters_widget))
        filters_layout.addWidget(self.status_filter)
        filters_layout.addWidget(QLabel("💳 Dívida:", filters_widget))
        filters_layout.addWidget(self.debt_filter)
        filters_layout.addWidget(self.add_button)
        filters_layout.addWidget(self.refresh_button)
        filters_layout.addWidget(self.delete_button)

        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(filters_widget)

        self.message_label = QLabel(
            "Conecte-se ao banco de dados para visualizar os cidadãos.",
            self,
        )
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet("color: #696969; font-size: 12px;")

        self.content_container = QWidget(self)
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        stats_frame = QWidget(self.content_container)
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(12)

        self.total_card = SummaryCard("👥 Total Cidadãos", 0, "R$ 0,00", self.colors["primary"], stats_frame)
        self.active_card = SummaryCard("✅ Ativos", 0, "0%", self.colors["success"], stats_frame)
        self.inactive_card = SummaryCard("🔴 Inativos", 0, "R$ 0,00", self.colors["warning"], stats_frame)

        stats_layout.addWidget(self.total_card)
        stats_layout.addWidget(self.active_card)
        stats_layout.addWidget(self.inactive_card)

        self.table = QTableWidget(self.content_container)
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Nome",
                "Email",
                "CPF",
                "Telefone",
                "Endereço",
                "Saldo",
                "Dívida",
                "Status",
                "Username",
            ]
        )
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)

        info_frame = QFrame(self.content_container)
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(8, 4, 8, 4)

        self.info_label = QLabel("👥 0 cidadãos registrados", info_frame)
        self.info_label.setStyleSheet("color: #696969; font-size: 11px;")

        info_layout.addWidget(self.info_label)
        info_layout.addStretch(1)

        content_layout.addWidget(stats_frame)
        content_layout.addWidget(self.table, 1)
        content_layout.addWidget(info_frame)

        layout.addWidget(header)
        layout.addWidget(self.message_label)
        layout.addWidget(self.content_container, 1)

        self.set_connected(False)

    def set_connected(self, connected):
        self.message_label.setVisible(not connected)
        self.content_container.setVisible(connected)

    def load_citizens(self):
        if not self.app.connected:
            self.set_connected(False)
            return

        try:
            conn_string = self.app.get_connection_string()
            with psy.connect(conn_string) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        """
                        SELECT c.id, c.first_name, c.last_name, c.email, c.cpf, c.phone,
                               c.address, c.birth_date, c.wallet_balance, c.debt, c.allowed,
                               u.username, c.created_at
                        FROM citizen_active c
                        JOIN app_user u ON c.app_user_id = u.id
                        ORDER BY c.first_name, c.last_name
                        """
                    )
                    self.all_citizens = cur.fetchall()

            self.set_connected(True)
            self.update_stats(self.all_citizens)
            self.apply_filters()
            self.app.status_label.setText("Cidadãos carregados")
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar cidadãos: {exc}")

    def update_stats(self, citizens):
        total_citizens = len(citizens)
        active_citizens = len([c for c in citizens if c["allowed"]]) if citizens else 0
        inactive_citizens = len([c for c in citizens if not c["allowed"]]) if citizens else 0
        total_balance = sum(c["wallet_balance"] for c in citizens if c["wallet_balance"]) if citizens else 0
        total_debt = sum(c["debt"] for c in citizens if c["debt"]) if citizens else 0

        active_percent = f"{(active_citizens / total_citizens * 100):.1f}%" if total_citizens else "0%"

        self.total_card.update(total_citizens, format_currency_brl(total_balance))
        self.active_card.update(active_citizens, active_percent)
        self.inactive_card.update(inactive_citizens, format_currency_brl(total_debt))

    def apply_filters(self):
        if not self.all_citizens:
            self.update_table([])
            self.update_info_label([])
            return

        filtered = self.all_citizens

        name_filter = self.name_filter.text().lower().strip()
        if name_filter:
            filtered = [
                c
                for c in filtered
                if (c["first_name"] and name_filter in c["first_name"].lower())
                or (c["last_name"] and name_filter in c["last_name"].lower())
            ]

        cpf_filter = self.cpf_filter.text().strip()
        if cpf_filter:
            filtered = [c for c in filtered if c["cpf"] and cpf_filter in c["cpf"]]

        status_filter = self.status_filter.currentText()
        if status_filter == "Ativos":
            filtered = [c for c in filtered if c["allowed"]]
        elif status_filter == "Inativos":
            filtered = [c for c in filtered if not c["allowed"]]

        debt_filter = self.debt_filter.currentText()
        if debt_filter == "Com Dívida":
            filtered = [c for c in filtered if c.get("debt", 0) > 0]
        elif debt_filter == "Sem Dívida":
            filtered = [c for c in filtered if c.get("debt", 0) == 0]

        self.filtered_citizens = filtered
        self.update_table(filtered)
        self.update_info_label(filtered)

    def update_table(self, citizens):
        self.table.setRowCount(0)
        for citizen in citizens:
            row = self.table.rowCount()
            self.table.insertRow(row)

            full_name = f"{citizen['first_name']} {citizen['last_name']}"
            status = "✅ Ativo" if citizen["allowed"] else "🔴 Inativo"

            values = [
                citizen["id"],
                full_name,
                citizen["email"] or "N/A",
                citizen["cpf"] or "N/A",
                citizen["phone"] or "N/A",
                citizen["address"] or "N/A",
                format_currency_brl(citizen["wallet_balance"]) if citizen["wallet_balance"] else "R$ 0,00",
                format_currency_brl(citizen["debt"]) if citizen["debt"] else "R$ 0,00",
                status,
                citizen["username"] or "N/A",
            ]

            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.table.setItem(row, col, item)

    def update_info_label(self, citizens):
        total = len(self.all_citizens)
        count = len(citizens)
        if count != total and self.has_active_filters():
            self.info_label.setText(f"👥 {count} cidadãos registrados ({total} total)")
        else:
            self.info_label.setText(f"👥 {count} cidadãos registrados")

    def has_active_filters(self):
        return any(
            [
                self.name_filter.text().strip(),
                self.cpf_filter.text().strip(),
                self.status_filter.currentText() != "Todos",
                self.debt_filter.currentText() != "Todos",
            ]
        )

    def open_add_dialog(self):
        if not self.app.connected:
            QMessageBox.warning(self, "Aviso", "Conecte-se ao banco de dados primeiro!")
            return

        dialog = AddCitizenDialog(self.app, self)
        if dialog.exec() == QDialog.Accepted:
            self.load_citizens()

    def delete_selected(self):
        if not self.app.connected:
            QMessageBox.warning(self, "Aviso", "Conecte-se ao banco de dados primeiro!")
            return

        selection = self.table.selectionModel().selectedRows()
        if not selection:
            QMessageBox.warning(self, "Aviso", "Selecione um cidadão para excluir!")
            return

        row = selection[0].row()
        citizen_id = self.table.item(row, 0).text()
        citizen_name = self.table.item(row, 1).text()

        confirm = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o cidadão:\n\n{citizen_name} (ID: {citizen_id})\n\n"
            "Esta ação não poderá ser desfeita!",
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            conn_string = self.app.get_connection_string()
            with psy.connect(conn_string) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT COUNT(*) FROM fine WHERE citizen_id = %s AND status = 'pending'",
                        (citizen_id,),
                    )
                    pending_fines = cur.fetchone()[0]
                    if pending_fines > 0:
                        QMessageBox.critical(
                            self,
                            "Erro",
                            f"Não é possível excluir cidadão com {pending_fines} multa(s) pendente(s)!",
                        )
                        return

                    cur.execute("DELETE FROM citizen WHERE id = %s", (citizen_id,))
                conn.commit()

            QMessageBox.information(
                self, "Sucesso", f"Cidadão {citizen_name} excluído com sucesso!"
            )
            self.load_citizens()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao excluir cidadão: {exc}")


class VehiclesPage(QWidget):
    """Página de Gestão de Veículos."""

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.colors = app.colors
        self.fonts = app.fonts
        self.all_vehicles = []
        self.filtered_vehicles = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QFrame(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(12)

        title_label = QLabel("🚗 Gestão de Veículos", header)
        title_label.setStyleSheet("font-size: 16px; font-weight: 700;")

        filters_widget = QWidget(header)
        filters_layout = QHBoxLayout(filters_widget)
        filters_layout.setContentsMargins(0, 0, 0, 0)
        filters_layout.setSpacing(8)

        self.plate_filter = QLineEdit(filters_widget)
        self.plate_filter.setPlaceholderText("Placa")
        self.plate_filter.textChanged.connect(self.apply_filters)

        self.model_filter = QLineEdit(filters_widget)
        self.model_filter.setPlaceholderText("Modelo")
        self.model_filter.textChanged.connect(self.apply_filters)

        self.year_filter = QLineEdit(filters_widget)
        self.year_filter.setPlaceholderText("Ano")
        self.year_filter.textChanged.connect(self.apply_filters)

        self.status_filter = QComboBox(filters_widget)
        self.status_filter.addItems(["Todos", "Ativos", "Inativos"])
        self.status_filter.currentIndexChanged.connect(self.apply_filters)

        self.add_button = QPushButton("➕ Adicionar", filters_widget)
        self.add_button.setObjectName("SuccessButton")
        self.add_button.clicked.connect(self.open_add_dialog)

        self.refresh_button = QPushButton("🔄 Atualizar", filters_widget)
        self.refresh_button.setObjectName("PrimaryButton")
        self.refresh_button.clicked.connect(self.load_vehicles)

        self.delete_button = QPushButton("❌ Excluir", filters_widget)
        self.delete_button.setObjectName("DangerButton")
        self.delete_button.clicked.connect(self.delete_selected)

        filters_layout.addWidget(QLabel("🔍 Placa:", filters_widget))
        filters_layout.addWidget(self.plate_filter)
        filters_layout.addWidget(QLabel("🚗 Modelo:", filters_widget))
        filters_layout.addWidget(self.model_filter)
        filters_layout.addWidget(QLabel("📅 Ano:", filters_widget))
        filters_layout.addWidget(self.year_filter)
        filters_layout.addWidget(QLabel("Status:", filters_widget))
        filters_layout.addWidget(self.status_filter)
        filters_layout.addWidget(self.add_button)
        filters_layout.addWidget(self.refresh_button)
        filters_layout.addWidget(self.delete_button)

        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(filters_widget)

        self.message_label = QLabel(
            "Conecte-se ao banco de dados para visualizar os veículos.",
            self,
        )
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet("color: #696969; font-size: 12px;")

        self.content_container = QWidget(self)
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        stats_frame = QWidget(self.content_container)
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(12)

        self.total_card = SummaryCard("🚗 Total Veículos", 0, "100%", self.colors["primary"], stats_frame)
        self.active_card = SummaryCard("✅ Ativos", 0, "0%", self.colors["success"], stats_frame)
        self.inactive_card = SummaryCard("🔴 Inativos", 0, "0%", self.colors["warning"], stats_frame)

        stats_layout.addWidget(self.total_card)
        stats_layout.addWidget(self.active_card)
        stats_layout.addWidget(self.inactive_card)

        self.table = QTableWidget(self.content_container)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Placa", "Modelo", "Ano", "Proprietário", "Status"]
        )
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)

        info_frame = QFrame(self.content_container)
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(8, 4, 8, 4)

        self.info_label = QLabel("🚗 0 veículos registrados", info_frame)
        self.info_label.setStyleSheet("color: #696969; font-size: 11px;")

        info_layout.addWidget(self.info_label)
        info_layout.addStretch(1)

        content_layout.addWidget(stats_frame)
        content_layout.addWidget(self.table, 1)
        content_layout.addWidget(info_frame)

        layout.addWidget(header)
        layout.addWidget(self.message_label)
        layout.addWidget(self.content_container, 1)

        self.set_connected(False)

    def set_connected(self, connected):
        self.message_label.setVisible(not connected)
        self.content_container.setVisible(connected)

    def load_vehicles(self):
        if not self.app.connected:
            self.set_connected(False)
            return

        try:
            conn_string = self.app.get_connection_string()
            with psy.connect(conn_string) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        """
                        SELECT v.id, v.license_plate, v.model, v.year, v.allowed,
                               u.username, c.first_name, c.last_name
                        FROM vehicle_active v
                        JOIN app_user u ON v.app_user_id = u.id
                        LEFT JOIN citizen_active c ON v.citizen_id = c.id
                        ORDER BY v.license_plate
                        """
                    )
                    self.all_vehicles = cur.fetchall()

            self.set_connected(True)
            self.update_stats(self.all_vehicles)
            self.apply_filters()
            self.app.status_label.setText("Veículos carregados")
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar veículos: {exc}")

    def update_stats(self, vehicles):
        total = len(vehicles)
        active = len([v for v in vehicles if v["allowed"]]) if vehicles else 0
        inactive = len([v for v in vehicles if not v["allowed"]]) if vehicles else 0

        active_percent = f"{(active / total * 100):.1f}%" if total else "0%"
        inactive_percent = f"{(inactive / total * 100):.1f}%" if total else "0%"

        self.total_card.update(total, "100%" if total else "0%")
        self.active_card.update(active, active_percent)
        self.inactive_card.update(inactive, inactive_percent)

    def apply_filters(self):
        if not self.all_vehicles:
            self.update_table([])
            self.update_info_label([])
            return

        filtered = self.all_vehicles

        plate_filter = self.plate_filter.text().upper().strip()
        if plate_filter:
            filtered = [
                v
                for v in filtered
                if v["license_plate"]
                and plate_filter in v["license_plate"].upper()
            ]

        model_filter = self.model_filter.text().lower().strip()
        if model_filter:
            filtered = [
                v
                for v in filtered
                if v["model"] and model_filter in v["model"].lower()
            ]

        year_filter = self.year_filter.text().strip()
        if year_filter:
            filtered = [
                v
                for v in filtered
                if v["year"] and year_filter in str(v["year"])
            ]

        status_filter = self.status_filter.currentText()
        if status_filter == "Ativos":
            filtered = [v for v in filtered if v["allowed"]]
        elif status_filter == "Inativos":
            filtered = [v for v in filtered if not v["allowed"]]

        self.filtered_vehicles = filtered
        self.update_table(filtered)
        self.update_info_label(filtered)

    def update_table(self, vehicles):
        self.table.setRowCount(0)
        for vehicle in vehicles:
            row = self.table.rowCount()
            self.table.insertRow(row)

            if vehicle["first_name"] and vehicle["last_name"]:
                owner_name = f"{vehicle['first_name']} {vehicle['last_name']}"
            else:
                owner_name = vehicle["username"] or "N/A"

            status = "✅ Ativo" if vehicle["allowed"] else "🔴 Inativo"

            values = [
                vehicle["id"],
                vehicle["license_plate"] or "N/A",
                vehicle["model"] or "N/A",
                vehicle["year"] or "N/A",
                owner_name,
                status,
            ]

            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.table.setItem(row, col, item)

    def update_info_label(self, vehicles):
        total = len(self.all_vehicles)
        count = len(vehicles)
        if count != total and self.has_active_filters():
            self.info_label.setText(f"🚗 {count} veículos registrados ({total} total)")
        else:
            self.info_label.setText(f"🚗 {count} veículos registrados")

    def has_active_filters(self):
        return any(
            [
                self.plate_filter.text().strip(),
                self.model_filter.text().strip(),
                self.year_filter.text().strip(),
                self.status_filter.currentText() != "Todos",
            ]
        )

    def open_add_dialog(self):
        if not self.app.connected:
            QMessageBox.warning(self, "Aviso", "Conecte-se ao banco de dados primeiro!")
            return

        dialog = AddVehicleDialog(self.app, self)
        if dialog.exec() == QDialog.Accepted:
            self.load_vehicles()

    def delete_selected(self):
        if not self.app.connected:
            QMessageBox.warning(self, "Aviso", "Conecte-se ao banco de dados primeiro!")
            return

        selection = self.table.selectionModel().selectedRows()
        if not selection:
            QMessageBox.warning(self, "Aviso", "Selecione um veículo para excluir!")
            return

        row = selection[0].row()
        vehicle_id = self.table.item(row, 0).text()
        license_plate = self.table.item(row, 1).text()
        model = self.table.item(row, 2).text()

        confirm = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o veículo:\n\n{model} - Placa: {license_plate} (ID: {vehicle_id})\n\n"
            "Esta ação não poderá ser desfeita!",
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            conn_string = self.app.get_connection_string()
            with psy.connect(conn_string) as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM vehicle WHERE id = %s", (vehicle_id,))
                conn.commit()

            QMessageBox.information(
                self,
                "Sucesso",
                f"Veículo {license_plate} excluído com sucesso!",
            )
            self.load_vehicles()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao excluir veículo: {exc}")


class SensorsPage(QWidget):
    """Página de Gestão de Sensores."""

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.colors = app.colors
        self.fonts = app.fonts
        self.all_sensors = []
        self.filtered_sensors = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QFrame(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(12)

        title_label = QLabel("📹 Gestão de Sensores", header)
        title_label.setStyleSheet("font-size: 16px; font-weight: 700;")

        filters_widget = QWidget(header)
        filters_layout = QHBoxLayout(filters_widget)
        filters_layout.setContentsMargins(0, 0, 0, 0)
        filters_layout.setSpacing(8)

        self.type_filter = QLineEdit(filters_widget)
        self.type_filter.setPlaceholderText("Tipo")
        self.type_filter.textChanged.connect(self.apply_filters)

        self.location_filter = QLineEdit(filters_widget)
        self.location_filter.setPlaceholderText("Localização")
        self.location_filter.textChanged.connect(self.apply_filters)

        self.status_filter = QComboBox(filters_widget)
        self.status_filter.addItems(["Todos", "Ativos", "Inativos"])
        self.status_filter.currentIndexChanged.connect(self.apply_filters)

        self.readings_filter = QComboBox(filters_widget)
        self.readings_filter.addItems(["Todos", "Com Leituras", "Sem Leituras"])
        self.readings_filter.currentIndexChanged.connect(self.apply_filters)

        self.add_button = QPushButton("➕ Adicionar", filters_widget)
        self.add_button.setObjectName("SuccessButton")
        self.add_button.clicked.connect(self.open_add_dialog)

        self.refresh_button = QPushButton("🔄 Atualizar", filters_widget)
        self.refresh_button.setObjectName("PrimaryButton")
        self.refresh_button.clicked.connect(self.load_sensors)

        self.delete_button = QPushButton("❌ Excluir", filters_widget)
        self.delete_button.setObjectName("DangerButton")
        self.delete_button.clicked.connect(self.delete_selected)

        filters_layout.addWidget(QLabel("🔍 Tipo:", filters_widget))
        filters_layout.addWidget(self.type_filter)
        filters_layout.addWidget(QLabel("📍 Local:", filters_widget))
        filters_layout.addWidget(self.location_filter)
        filters_layout.addWidget(QLabel("Status:", filters_widget))
        filters_layout.addWidget(self.status_filter)
        filters_layout.addWidget(QLabel("📊 Leituras:", filters_widget))
        filters_layout.addWidget(self.readings_filter)
        filters_layout.addWidget(self.add_button)
        filters_layout.addWidget(self.refresh_button)
        filters_layout.addWidget(self.delete_button)

        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(filters_widget)

        self.message_label = QLabel(
            "Conecte-se ao banco de dados para visualizar os sensores.",
            self,
        )
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet("color: #696969; font-size: 12px;")

        self.content_container = QWidget(self)
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        stats_frame = QWidget(self.content_container)
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(12)

        self.total_card = SummaryCard("📹 Total Sensores", 0, "0 leituras", self.colors["primary"], stats_frame)
        self.active_card = SummaryCard("✅ Ativos", 0, "0%", self.colors["success"], stats_frame)
        self.inactive_card = SummaryCard("🔴 Inativos", 0, "0%", self.colors["warning"], stats_frame)

        stats_layout.addWidget(self.total_card)
        stats_layout.addWidget(self.active_card)
        stats_layout.addWidget(self.inactive_card)

        self.table = QTableWidget(self.content_container)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Tipo", "Localização", "Status", "Leituras", "Última Leitura"]
        )
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)

        info_frame = QFrame(self.content_container)
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(8, 4, 8, 4)

        self.info_label = QLabel("📊 0 sensores cadastrados", info_frame)
        self.info_label.setStyleSheet("color: #696969; font-size: 11px;")

        info_layout.addWidget(self.info_label)
        info_layout.addStretch(1)

        content_layout.addWidget(stats_frame)
        content_layout.addWidget(self.table, 1)
        content_layout.addWidget(info_frame)

        layout.addWidget(header)
        layout.addWidget(self.message_label)
        layout.addWidget(self.content_container, 1)

        self.set_connected(False)

    def set_connected(self, connected):
        self.message_label.setVisible(not connected)
        self.content_container.setVisible(connected)

    def load_sensors(self):
        if not self.app.connected:
            self.set_connected(False)
            return

        try:
            conn_string = self.app.get_connection_string()
            with psy.connect(conn_string) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        """
                        SELECT s.id, s.type, s.location, s.active,
                               COUNT(r.id) as reading_count,
                               MAX(r.timestamp) as last_reading
                        FROM sensor_active s
                        LEFT JOIN reading r ON s.id = r.sensor_id
                        GROUP BY s.id, s.type, s.location, s.active
                        ORDER BY s.type, s.location
                        """
                    )
                    self.all_sensors = cur.fetchall()

            self.set_connected(True)
            self.update_stats(self.all_sensors)
            self.apply_filters()
            self.app.status_label.setText("Sensores carregados")
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar sensores: {exc}")

    def update_stats(self, sensors):
        total = len(sensors)
        active = len([s for s in sensors if s["active"]]) if sensors else 0
        inactive = len([s for s in sensors if not s["active"]]) if sensors else 0
        total_readings = sum(s["reading_count"] for s in sensors if s["reading_count"]) if sensors else 0

        active_percent = f"{(active / total * 100):.1f}%" if total else "0%"
        inactive_percent = f"{(inactive / total * 100):.1f}%" if total else "0%"

        self.total_card.update(total, f"{total_readings} leituras")
        self.active_card.update(active, active_percent)
        self.inactive_card.update(inactive, inactive_percent)

    def apply_filters(self):
        if not self.all_sensors:
            self.update_table([])
            self.update_info_label([])
            return

        filtered = self.all_sensors

        type_filter = self.type_filter.text().lower().strip()
        if type_filter:
            filtered = [
                s for s in filtered if s["type"] and type_filter in s["type"].lower()
            ]

        location_filter = self.location_filter.text().lower().strip()
        if location_filter:
            filtered = [
                s
                for s in filtered
                if s["location"] and location_filter in s["location"].lower()
            ]

        status_filter = self.status_filter.currentText()
        if status_filter == "Ativos":
            filtered = [s for s in filtered if s["active"]]
        elif status_filter == "Inativos":
            filtered = [s for s in filtered if not s["active"]]

        readings_filter = self.readings_filter.currentText()
        if readings_filter == "Com Leituras":
            filtered = [
                s for s in filtered if s.get("reading_count") and s["reading_count"] > 0
            ]
        elif readings_filter == "Sem Leituras":
            filtered = [
                s for s in filtered if not s.get("reading_count") or s["reading_count"] == 0
            ]

        self.filtered_sensors = filtered
        self.update_table(filtered)
        self.update_info_label(filtered)

    def update_table(self, sensors):
        self.table.setRowCount(0)
        for sensor in sensors:
            row = self.table.rowCount()
            self.table.insertRow(row)

            status = "🟢 Ativo" if sensor["active"] else "🔴 Inativo"
            if sensor["last_reading"] and hasattr(sensor["last_reading"], "strftime"):
                last_reading = sensor["last_reading"].strftime("%d/%m/%Y %H:%M")
            else:
                last_reading = "N/A"

            values = [
                sensor["id"],
                sensor["type"] or "N/A",
                sensor["location"] or "N/A",
                status,
                sensor["reading_count"] if sensor["reading_count"] is not None else 0,
                last_reading,
            ]

            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.table.setItem(row, col, item)

    def update_info_label(self, sensors):
        total = len(self.all_sensors)
        count = len(sensors)
        if count != total and self.has_active_filters():
            self.info_label.setText(f"📊 {count} sensores cadastrados ({total} total)")
        else:
            self.info_label.setText(f"📊 {count} sensores cadastrados")

    def has_active_filters(self):
        return any(
            [
                self.type_filter.text().strip(),
                self.location_filter.text().strip(),
                self.status_filter.currentText() != "Todos",
                self.readings_filter.currentText() != "Todos",
            ]
        )

    def open_add_dialog(self):
        if not self.app.connected:
            QMessageBox.warning(self, "Aviso", "Conecte-se ao banco de dados primeiro!")
            return

        dialog = AddSensorDialog(self.app, self)
        if dialog.exec() == QDialog.Accepted:
            self.load_sensors()

    def delete_selected(self):
        if not self.app.connected:
            QMessageBox.warning(self, "Aviso", "Conecte-se ao banco de dados primeiro!")
            return

        selection = self.table.selectionModel().selectedRows()
        if not selection:
            QMessageBox.warning(self, "Aviso", "Selecione um sensor para excluir!")
            return

        row = selection[0].row()
        sensor_id = self.table.item(row, 0).text()
        sensor_type = self.table.item(row, 1).text()
        location = self.table.item(row, 2).text()

        confirm = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o sensor:\n\n{sensor_type} - {location} (ID: {sensor_id})\n\n"
            "Esta ação não poderá ser desfeita!",
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            conn_string = self.app.get_connection_string()
            with psy.connect(conn_string) as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM sensor WHERE id = %s", (sensor_id,))
                conn.commit()

            QMessageBox.information(
                self,
                "Sucesso",
                f"Sensor {sensor_type} excluído com sucesso!",
            )
            self.load_sensors()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao excluir sensor: {exc}")


class IncidentsPage(QWidget):
    """Página de Gestão de Incidentes."""

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.colors = app.colors
        self.fonts = app.fonts
        self.all_incidents = []
        self.filtered_incidents = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QFrame(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(12)

        title_label = QLabel("⚠️ Gestão de Incidentes", header)
        title_label.setStyleSheet("font-size: 16px; font-weight: 700;")

        filters_widget = QWidget(header)
        filters_layout = QHBoxLayout(filters_widget)
        filters_layout.setContentsMargins(0, 0, 0, 0)
        filters_layout.setSpacing(8)

        self.location_filter = QLineEdit(filters_widget)
        self.location_filter.setPlaceholderText("Localização")
        self.location_filter.textChanged.connect(self.apply_filters)

        self.period_filter = QComboBox(filters_widget)
        self.period_filter.addItems(["Todos", "Hoje", "Esta Semana", "Este Mês"])
        self.period_filter.currentIndexChanged.connect(self.apply_filters)

        self.fines_filter = QComboBox(filters_widget)
        self.fines_filter.addItems(["Todos", "Com Multas", "Sem Multas"])
        self.fines_filter.currentIndexChanged.connect(self.apply_filters)

        self.description_filter = QLineEdit(filters_widget)
        self.description_filter.setPlaceholderText("Descrição")
        self.description_filter.textChanged.connect(self.apply_filters)

        self.add_button = QPushButton("➕ Registrar", filters_widget)
        self.add_button.setObjectName("WarningButton")
        self.add_button.clicked.connect(self.open_add_dialog)

        self.refresh_button = QPushButton("🔄 Atualizar", filters_widget)
        self.refresh_button.setObjectName("PrimaryButton")
        self.refresh_button.clicked.connect(self.load_incidents)

        filters_layout.addWidget(QLabel("🔍 Local:", filters_widget))
        filters_layout.addWidget(self.location_filter)
        filters_layout.addWidget(QLabel("📅 Período:", filters_widget))
        filters_layout.addWidget(self.period_filter)
        filters_layout.addWidget(QLabel("💰 Multas:", filters_widget))
        filters_layout.addWidget(self.fines_filter)
        filters_layout.addWidget(QLabel("📝 Descrição:", filters_widget))
        filters_layout.addWidget(self.description_filter)
        filters_layout.addWidget(self.add_button)
        filters_layout.addWidget(self.refresh_button)

        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(filters_widget)

        self.message_label = QLabel(
            "Conecte-se ao banco de dados para visualizar os incidentes.",
            self,
        )
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet("color: #696969; font-size: 12px;")

        self.content_container = QWidget(self)
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        stats_frame = QWidget(self.content_container)
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(12)

        self.total_card = SummaryCard("⚠️ Total Incidentes", 0, "0 esta semana", self.colors["accent"], stats_frame)
        self.fines_card = SummaryCard("💰 Multas Geradas", 0, "R$ 0,00", self.colors["secondary"], stats_frame)
        self.avg_card = SummaryCard("📊 Média/Dia", "0", "Últimos 30 dias", self.colors["primary"], stats_frame)

        stats_layout.addWidget(self.total_card)
        stats_layout.addWidget(self.fines_card)
        stats_layout.addWidget(self.avg_card)

        self.table = QTableWidget(self.content_container)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Local", "Data/Hora", "Descrição", "Multas", "Valor Total"]
        )
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)

        info_frame = QFrame(self.content_container)
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(8, 4, 8, 4)

        self.info_label = QLabel("⚠️ 0 incidentes registrados", info_frame)
        self.info_label.setStyleSheet("color: #696969; font-size: 11px;")

        info_layout.addWidget(self.info_label)
        info_layout.addStretch(1)

        content_layout.addWidget(stats_frame)
        content_layout.addWidget(self.table, 1)
        content_layout.addWidget(info_frame)

        layout.addWidget(header)
        layout.addWidget(self.message_label)
        layout.addWidget(self.content_container, 1)

        self.set_connected(False)

    def set_connected(self, connected):
        self.message_label.setVisible(not connected)
        self.content_container.setVisible(connected)

    def load_incidents(self):
        if not self.app.connected:
            self.set_connected(False)
            return

        try:
            conn_string = self.app.get_connection_string()
            with psy.connect(conn_string) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        """
                        SELECT ti.id, ti.location, ti.occurred_at, ti.description,
                               COUNT(f.id) as fine_count,
                               COALESCE(SUM(f.amount), 0) as total_fines
                        FROM traffic_incident ti
                        LEFT JOIN fine f ON ti.id = f.traffic_incident_id
                        GROUP BY ti.id, ti.location, ti.occurred_at, ti.description
                        ORDER BY ti.occurred_at DESC
                        """
                    )
                    self.all_incidents = cur.fetchall()

            self.set_connected(True)
            self.update_stats(self.all_incidents)
            self.apply_filters()
            self.app.status_label.setText("Incidentes carregados")
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar incidentes: {exc}")

    def update_stats(self, incidents):
        total = len(incidents)
        week_ago = datetime.now() - timedelta(days=7)
        this_week = len(
            [i for i in incidents if i["occurred_at"] and i["occurred_at"] >= week_ago]
        )
        total_fines = sum(i["fine_count"] or 0 for i in incidents)
        total_fines_amount = sum(i["total_fines"] or 0 for i in incidents)

        avg_day = f"{total / 30:.1f}" if total else "0"

        self.total_card.update(total, f"{this_week} esta semana")
        self.fines_card.update(total_fines, format_currency_brl(total_fines_amount))
        self.avg_card.update(avg_day, "Últimos 30 dias")

    def apply_filters(self):
        if not self.all_incidents:
            self.update_table([])
            self.update_info_label([])
            return

        filtered = self.all_incidents

        location_filter = self.location_filter.text().lower().strip()
        if location_filter:
            filtered = [
                i
                for i in filtered
                if i["location"] and location_filter in i["location"].lower()
            ]

        period_filter = self.period_filter.currentText()
        if period_filter != "Todos":
            now = datetime.now()
            if period_filter == "Hoje":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                filtered = [
                    i
                    for i in filtered
                    if i["occurred_at"] and i["occurred_at"].date() >= start_date.date()
                ]
            elif period_filter == "Esta Semana":
                start_date = now - timedelta(days=7)
                filtered = [
                    i
                    for i in filtered
                    if i["occurred_at"] and i["occurred_at"] >= start_date
                ]
            elif period_filter == "Este Mês":
                start_date = now - timedelta(days=30)
                filtered = [
                    i
                    for i in filtered
                    if i["occurred_at"] and i["occurred_at"] >= start_date
                ]

        fines_filter = self.fines_filter.currentText()
        if fines_filter == "Com Multas":
            filtered = [i for i in filtered if i["fine_count"] and i["fine_count"] > 0]
        elif fines_filter == "Sem Multas":
            filtered = [
                i for i in filtered if not i["fine_count"] or i["fine_count"] == 0
            ]

        description_filter = self.description_filter.text().lower().strip()
        if description_filter:
            filtered = [
                i
                for i in filtered
                if i["description"] and description_filter in i["description"].lower()
            ]

        self.filtered_incidents = filtered
        self.update_table(filtered)
        self.update_info_label(filtered)

    def update_table(self, incidents):
        self.table.setRowCount(0)
        for incident in incidents:
            row = self.table.rowCount()
            self.table.insertRow(row)

            occurred_at = (
                incident["occurred_at"].strftime("%d/%m %H:%M")
                if incident["occurred_at"]
                else "N/A"
            )
            description = incident["description"] or "Sem descrição"
            if len(description) > 50:
                description = description[:47] + "..."

            total_fines = (
                format_currency_brl(incident["total_fines"])
                if incident["total_fines"] and incident["total_fines"] > 0
                else "R$ 0,00"
            )

            values = [
                incident["id"],
                incident["location"] or "N/A",
                occurred_at,
                description,
                incident["fine_count"] or 0,
                total_fines,
            ]

            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.table.setItem(row, col, item)

    def update_info_label(self, incidents):
        total = len(self.all_incidents)
        count = len(incidents)
        if count != total and self.has_active_filters():
            self.info_label.setText(f"⚠️ {count} incidentes registrados ({total} total)")
        else:
            self.info_label.setText(f"⚠️ {count} incidentes registrados")

    def has_active_filters(self):
        return any(
            [
                self.location_filter.text().strip(),
                self.period_filter.currentText() != "Todos",
                self.fines_filter.currentText() != "Todos",
                self.description_filter.text().strip(),
            ]
        )

    def open_add_dialog(self):
        if not self.app.connected:
            QMessageBox.warning(self, "Aviso", "Conecte-se ao banco de dados primeiro!")
            return

        dialog = AddIncidentDialog(self.app, self)
        if dialog.exec() == QDialog.Accepted:
            self.load_incidents()


class FinesPage(QWidget):
    """Página de Gestão de Multas."""

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.colors = app.colors
        self.all_fines = []
        self.filtered_fines = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QFrame(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(12)

        title_label = QLabel("💰 Gestão de Multas", header)
        title_label.setStyleSheet("font-size: 16px; font-weight: 700;")

        controls_widget = QWidget(header)
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)

        self.status_filter = QComboBox(controls_widget)
        self.status_filter.addItems(["Todos", "Pendentes", "Pagas", "Vencidas"])
        self.status_filter.currentIndexChanged.connect(self.apply_filters)

        self.amount_filter = QLineEdit(controls_widget)
        self.amount_filter.setPlaceholderText("Valor mínimo")
        self.amount_filter.textChanged.connect(self.apply_filters)

        self.plate_filter = QLineEdit(controls_widget)
        self.plate_filter.setPlaceholderText("Placa")
        self.plate_filter.textChanged.connect(self.apply_filters)

        self.period_filter = QComboBox(controls_widget)
        self.period_filter.addItems(["Todos", "Hoje", "Esta Semana", "Este Mês", "Vencidas"])
        self.period_filter.currentIndexChanged.connect(self.apply_filters)

        self.pay_button = QPushButton("💳 Pagar", controls_widget)
        self.pay_button.setObjectName("SuccessButton")
        self.pay_button.clicked.connect(self.open_pay_dialog)

        self.generate_button = QPushButton("➕ Gerar", controls_widget)
        self.generate_button.setObjectName("WarningButton")
        self.generate_button.clicked.connect(self.open_generate_dialog)

        self.refresh_button = QPushButton("🔄 Atualizar", controls_widget)
        self.refresh_button.setObjectName("PrimaryButton")
        self.refresh_button.clicked.connect(self.load_fines)

        self.delete_button = QPushButton("🗑️ Excluir", controls_widget)
        self.delete_button.setObjectName("DangerButton")
        self.delete_button.clicked.connect(self.delete_selected)

        controls_layout.addWidget(QLabel("Status:", controls_widget))
        controls_layout.addWidget(self.status_filter)
        controls_layout.addWidget(QLabel("💰 Valor Mínimo:", controls_widget))
        controls_layout.addWidget(self.amount_filter)
        controls_layout.addWidget(QLabel("🚗 Placa:", controls_widget))
        controls_layout.addWidget(self.plate_filter)
        controls_layout.addWidget(QLabel("📅 Período:", controls_widget))
        controls_layout.addWidget(self.period_filter)
        controls_layout.addWidget(self.pay_button)
        controls_layout.addWidget(self.generate_button)
        controls_layout.addWidget(self.refresh_button)
        controls_layout.addWidget(self.delete_button)

        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(controls_widget)

        self.message_label = QLabel(
            "Conecte-se ao banco de dados para visualizar as multas.",
            self,
        )
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet("color: #696969; font-size: 12px;")

        self.content_container = QWidget(self)
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        stats_frame = QWidget(self.content_container)
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(12)

        self.total_card = SummaryCard("💰 Total Multas", 0, "R$ 0,00", self.colors["primary"], stats_frame)
        self.pending_card = SummaryCard("🔴 Pendentes", 0, "R$ 0,00", self.colors["warning"], stats_frame)
        self.overdue_card = SummaryCard("⚠️ Vencidas", 0, "R$ 0,00", self.colors["accent"], stats_frame)
        self.paid_card = SummaryCard("✅ Pagas", 0, "0%", self.colors["success"], stats_frame)

        stats_layout.addWidget(self.total_card)
        stats_layout.addWidget(self.pending_card)
        stats_layout.addWidget(self.overdue_card)
        stats_layout.addWidget(self.paid_card)

        self.table = QTableWidget(self.content_container)
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Valor", "Status", "Data", "Vencimento", "Local", "Descrição", "Placa", "Cidadão"]
        )
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)

        info_frame = QFrame(self.content_container)
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(8, 4, 8, 4)

        self.info_label = QLabel("💰 0 multas cadastradas", info_frame)
        self.info_label.setStyleSheet("color: #696969; font-size: 11px;")

        info_layout.addWidget(self.info_label)
        info_layout.addStretch(1)

        content_layout.addWidget(stats_frame)
        content_layout.addWidget(self.table, 1)
        content_layout.addWidget(info_frame)

        layout.addWidget(header)
        layout.addWidget(self.message_label)
        layout.addWidget(self.content_container, 1)

        self.set_connected(False)

    def set_connected(self, connected):
        self.message_label.setVisible(not connected)
        self.content_container.setVisible(connected)

    def load_fines(self):
        if not self.app.connected:
            self.set_connected(False)
            return

        try:
            conn_string = self.app.get_connection_string()
            with psy.connect(conn_string) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        """
                        SELECT f.id, f.amount, f.status, f.created_at, f.due_date,
                               ti.location as incident_location, ti.description as incident_description,
                               v.license_plate,
                               c.first_name, c.last_name
                        FROM fine f
                        LEFT JOIN traffic_incident ti ON f.traffic_incident_id = ti.id
                        LEFT JOIN vehicle v ON ti.vehicle_id = v.id
                        LEFT JOIN citizen c ON f.citizen_id = c.id
                        ORDER BY f.created_at DESC
                        """
                    )
                    self.all_fines = cur.fetchall()

            self.set_connected(True)
            self.update_stats(self.all_fines)
            self.apply_filters()
            self.app.status_label.setText("Multas carregadas")
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar multas: {exc}")

    def update_stats(self, fines):
        total_fines = len(fines)
        pending_fines = len([f for f in fines if f["status"] == "pending"])
        overdue_fines = len([f for f in fines if f["status"] == "overdue"])
        paid_fines = len([f for f in fines if f["status"] == "paid"])

        total_amount = sum(f["amount"] for f in fines if f["amount"]) if fines else 0
        pending_amount = sum(
            f["amount"] for f in fines if f["status"] == "pending" and f["amount"]
        )
        overdue_amount = sum(
            f["amount"] for f in fines if f["status"] == "overdue" and f["amount"]
        )

        paid_percent = f"{(paid_fines / total_fines * 100):.1f}%" if total_fines else "0%"

        self.total_card.update(total_fines, format_currency_brl(total_amount))
        self.pending_card.update(pending_fines, format_currency_brl(pending_amount))
        self.overdue_card.update(overdue_fines, format_currency_brl(overdue_amount))
        self.paid_card.update(paid_fines, paid_percent)

    def apply_filters(self):
        if not self.all_fines:
            self.update_table([])
            self.update_info_label([])
            return

        filtered = self.all_fines

        status_filter = self.status_filter.currentText()
        if status_filter == "Pendentes":
            filtered = [f for f in filtered if f["status"] == "pending"]
        elif status_filter == "Pagas":
            filtered = [f for f in filtered if f["status"] == "paid"]
        elif status_filter == "Vencidas":
            now_date = datetime.now().date()
            filtered = [
                f
                for f in filtered
                if f["due_date"] and f["due_date"] < now_date and f["status"] != "paid"
            ]

        amount_filter = self.amount_filter.text().strip()
        if amount_filter:
            try:
                min_amount = parse_money_input(amount_filter)
                filtered = [
                    f
                    for f in filtered
                    if f["amount"] and float(f["amount"]) >= min_amount
                ]
            except ValueError:
                pass

        plate_filter = self.plate_filter.text().upper().strip()
        if plate_filter:
            filtered = [
                f
                for f in filtered
                if f.get("license_plate")
                and plate_filter in f["license_plate"].upper()
            ]

        period_filter = self.period_filter.currentText()
        if period_filter != "Todos":
            now = datetime.now()
            if period_filter == "Hoje":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                filtered = [
                    f
                    for f in filtered
                    if f["created_at"] and f["created_at"].date() >= start_date.date()
                ]
            elif period_filter == "Esta Semana":
                start_date = now - timedelta(days=7)
                filtered = [
                    f
                    for f in filtered
                    if f["created_at"] and f["created_at"] >= start_date
                ]
            elif period_filter == "Este Mês":
                start_date = now - timedelta(days=30)
                filtered = [
                    f
                    for f in filtered
                    if f["created_at"] and f["created_at"] >= start_date
                ]
            elif period_filter == "Vencidas":
                now_date = now.date()
                filtered = [
                    f
                    for f in filtered
                    if f["due_date"] and f["due_date"] < now_date and f["status"] != "paid"
                ]

        self.filtered_fines = filtered
        self.update_table(filtered)
        self.update_info_label(filtered)

    def update_table(self, fines):
        self.table.setRowCount(0)
        status_map = {
            "pending": "🔴 Pendente",
            "paid": "✅ Paga",
            "overdue": "⚠️ Vencida",
            "cancelled": "❌ Cancelada",
        }

        for fine in fines:
            row = self.table.rowCount()
            self.table.insertRow(row)

            amount = (
                format_currency_brl(fine["amount"])
                if fine["amount"] and fine["amount"] > 0
                else "R$ 0,00"
            )
            created_at = (
                fine["created_at"].strftime("%d/%m/%Y") if fine["created_at"] else "N/A"
            )
            due_date = (
                fine["due_date"].strftime("%d/%m/%Y") if fine["due_date"] else "N/A"
            )
            incident_location = fine.get("incident_location", "N/A")
            incident_description = fine.get("incident_description", "N/A") or "N/A"
            if incident_description and len(incident_description) > 30:
                incident_description = incident_description[:27] + "..."
            license_plate = fine.get("license_plate", "N/A") or "N/A"

            citizen_name = "N/A"
            if fine.get("first_name") and fine.get("last_name"):
                citizen_name = f"{fine['first_name']} {fine['last_name']}"

            values = [
                fine["id"],
                amount,
                status_map.get(fine["status"], fine["status"]),
                created_at,
                due_date,
                incident_location,
                incident_description,
                license_plate,
                citizen_name,
            ]

            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.table.setItem(row, col, item)

    def update_info_label(self, fines):
        total = len(self.all_fines)
        count = len(fines)
        if count != total and self.has_active_filters():
            self.info_label.setText(f"💰 {count} multas cadastradas ({total} total)")
        else:
            self.info_label.setText(f"💰 {count} multas cadastradas")

    def has_active_filters(self):
        return any(
            [
                self.status_filter.currentText() != "Todos",
                self.amount_filter.text().strip(),
                self.plate_filter.text().strip(),
                self.period_filter.currentText() != "Todos",
            ]
        )

    def open_pay_dialog(self):
        if not self.app.connected:
            QMessageBox.warning(self, "Aviso", "Conecte-se ao banco de dados primeiro!")
            return

        dialog = PayFineDialog(self.app, self)
        if dialog.exec() == QDialog.Accepted:
            self.load_fines()

    def open_generate_dialog(self):
        if not self.app.connected:
            QMessageBox.warning(self, "Aviso", "Conecte-se ao banco de dados primeiro!")
            return

        dialog = GenerateFineDialog(self.app, self)
        if dialog.exec() == QDialog.Accepted:
            self.load_fines()

    def delete_selected(self):
        if not self.app.connected:
            QMessageBox.warning(self, "Aviso", "Conecte-se ao banco de dados primeiro!")
            return

        selection = self.table.selectionModel().selectedRows()
        if not selection:
            QMessageBox.warning(self, "Aviso", "Selecione uma multa para excluir!")
            return

        row = selection[0].row()
        fine_id = self.table.item(row, 0).text()
        amount = self.table.item(row, 1).text()
        status = self.table.item(row, 2).text()

        confirm = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir a multa:\n\nID: {fine_id} - Valor: {amount} - Status: {status}\n\n"
            "Esta ação não poderá ser desfeita!",
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            conn_string = self.app.get_connection_string()
            with psy.connect(conn_string) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT COUNT(*) FROM fine_payment WHERE fine_id = %s",
                        (fine_id,),
                    )
                    payments = cur.fetchone()[0]
                    if payments > 0:
                        QMessageBox.warning(
                            self,
                            "Erro",
                            f"Não é possível excluir multa com {payments} pagamento(s) registrado(s)!",
                        )
                        return

                    cur.execute("DELETE FROM fine WHERE id = %s", (fine_id,))
                conn.commit()

            QMessageBox.information(
                self, "Sucesso", f"Multa ID: {fine_id} excluída com sucesso!"
            )
            self.load_fines()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao excluir multa: {exc}")


class StatisticsPage(QWidget):
    """Página de Estatísticas do Sistema."""

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.colors = app.colors
        self.current_stats = None
        self.setObjectName("StatisticsPage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QFrame(self)
        header.setObjectName("StatsHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(12)

        title_label = QLabel("📈 Estatísticas do Sistema", header)
        title_label.setStyleSheet("font-size: 18px; font-weight: 700; color: #FFFFFF;")

        controls_widget = QWidget(header)
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)

        self.refresh_button = QPushButton("🔄 Atualizar", controls_widget)
        self.refresh_button.setObjectName("PrimaryButton")
        self.refresh_button.clicked.connect(self.load_statistics)

        self.export_button = QPushButton("📥 Exportar Relatório", controls_widget)
        self.export_button.setObjectName("SuccessButton")
        self.export_button.clicked.connect(self.export_statistics)

        controls_layout.addWidget(self.refresh_button)
        controls_layout.addWidget(self.export_button)

        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(controls_widget)

        self.message_label = QLabel(
            "Conecte-se ao banco de dados para visualizar estatísticas.",
            self,
        )
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet("color: #696969; font-size: 12px;")

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        content = QWidget(self.scroll_area)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        overview_header = self._build_section_header("VISÃO GERAL", content)
        content_layout.addWidget(overview_header)

        self.main_cards_container = QWidget(content)
        self.main_cards_layout = QGridLayout(self.main_cards_container)
        self.main_cards_layout.setContentsMargins(0, 0, 0, 0)
        self.main_cards_layout.setHorizontalSpacing(12)
        self.main_cards_layout.setVerticalSpacing(12)
        for col in range(3):
            self.main_cards_layout.setColumnStretch(col, 1)

        self.main_cards_block = QFrame(content)
        self.main_cards_block.setProperty("role", "stats_block")
        main_block_layout = QVBoxLayout(self.main_cards_block)
        main_block_layout.setContentsMargins(14, 14, 14, 14)
        main_block_layout.setSpacing(12)
        main_block_layout.addWidget(self.main_cards_container)

        content_layout.addWidget(self.main_cards_block)

        details_header = self._build_section_header("DETALHES E INDICADORES", content)
        content_layout.addWidget(details_header)

        details_container = QFrame(content)
        details_container.setProperty("role", "stats_block")
        details_layout = QHBoxLayout(details_container)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(16)

        left_frame = QWidget(details_container)
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(10)

        left_title = QLabel("📊 Tabelas Detalhadas", left_frame)
        left_title.setStyleSheet("font-weight: 600; color: #2F4F4F;")
        left_layout.addWidget(left_title)

        self.sensors_group, self.sensors_table = self._create_table_group(
            "📹 Sensores por Tipo",
            ["Tipo", "Total", "Ativos"],
            left_frame,
        )
        self.incidents_group, self.incidents_table = self._create_table_group(
            "⚠️ Incidentes por Localização",
            ["Localização", "Total", "Multas", "Multa Média"],
            left_frame,
        )
        self.fines_group, self.fines_table = self._create_table_group(
            "💰 Multas por Status",
            ["Status", "Quantidade", "Valor Total"],
            left_frame,
        )

        left_layout.addWidget(self.sensors_group)
        left_layout.addWidget(self.incidents_group)
        left_layout.addWidget(self.fines_group)
        left_layout.addStretch(1)

        right_frame = QWidget(details_container)
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(10)

        right_title = QLabel("📌 Indicadores-Chave", right_frame)
        right_title.setStyleSheet("font-weight: 600; color: #2F4F4F;")

        self.secondary_cards_container = QWidget(right_frame)
        self.secondary_cards_layout = QVBoxLayout(self.secondary_cards_container)
        self.secondary_cards_layout.setContentsMargins(0, 0, 0, 0)
        self.secondary_cards_layout.setSpacing(10)

        right_layout.addWidget(right_title)
        right_layout.addWidget(self.secondary_cards_container)
        right_layout.addStretch(1)

        details_layout.addWidget(left_frame, 2)
        details_layout.addWidget(right_frame, 1)

        content_layout.addWidget(details_container)
        content_layout.addStretch(1)

        self.scroll_area.setWidget(content)

        layout.addWidget(header)
        layout.addWidget(self.message_label)
        layout.addWidget(self.scroll_area, 1)

        self.set_connected(False)

    def set_connected(self, connected):
        self.message_label.setVisible(not connected)
        self.scroll_area.setVisible(connected)

    def _build_section_header(self, text, parent):
        container = QWidget(parent)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(8)

        label = QLabel(text, container)
        label.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #2F4F4F;"
        )

        line = QFrame(container)
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet(f"color: {self.colors['border']}; background: {self.colors['border']};")

        layout.addWidget(label)
        layout.addWidget(line, 1)
        return container

    def _create_table_group(self, title, columns, parent):
        group = QGroupBox(title, parent)
        group.setProperty("role", "stats_group")
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(8, 8, 8, 8)
        group_layout.setSpacing(6)

        table = QTableWidget(group)
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.setSortingEnabled(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table.horizontalHeader().setStretchLastSection(True)
        table.setMinimumHeight(160)

        group_layout.addWidget(table)
        return group, table

    def load_statistics(self):
        if not self.app.connected:
            self.set_connected(False)
            return

        try:
            conn_string = self.app.get_connection_string()
            with psy.connect(conn_string) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    stats = self._load_stats(cur)

            self.current_stats = stats
            self.set_connected(True)
            self.update_statistics(stats)
            self.app.status_label.setText("Estatísticas atualizadas")
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao carregar estatísticas: {exc}",
            )

    def _load_stats(self, cur):
        stats = {}

        try:
            cur.execute(
                """
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as this_month,
                       COUNT(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as this_week
                FROM app_user_active
                """
            )
            stats["users"] = cur.fetchone()
        except Exception:
            stats["users"] = {"total": 0, "this_month": 0, "this_week": 0}

        try:
            cur.execute(
                """
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN debt > 0 THEN 1 END) as with_debt,
                       COUNT(CASE WHEN allowed = TRUE THEN 1 END) as with_access,
                       COALESCE(SUM(debt), 0) as total_debt,
                       COALESCE(AVG(debt), 0) as avg_debt
                FROM citizen_active
                """
            )
            stats["citizens"] = cur.fetchone()
        except Exception:
            stats["citizens"] = {
                "total": 0,
                "with_debt": 0,
                "with_access": 0,
                "total_debt": 0,
                "avg_debt": 0,
            }

        try:
            cur.execute(
                """
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN allowed = TRUE THEN 1 END) as active,
                       COUNT(CASE WHEN allowed = FALSE THEN 1 END) as blocked,
                       COUNT(DISTINCT citizen_id) as unique_owners
                FROM vehicle_active
                """
            )
            stats["vehicles"] = cur.fetchone()
        except Exception:
            stats["vehicles"] = {
                "total": 0,
                "active": 0,
                "blocked": 0,
                "unique_owners": 0,
            }

        try:
            cur.execute(
                """
                SELECT type, COUNT(*) as count,
                       COUNT(CASE WHEN active = TRUE THEN 1 END) as active
                FROM sensor_active
                GROUP BY type
                ORDER BY count DESC
                """
            )
            stats["sensors_by_type"] = cur.fetchall()

            cur.execute(
                """
                SELECT COUNT(*) as total_sensors,
                       COUNT(CASE WHEN active = TRUE THEN 1 END) as active_sensors,
                       COUNT(DISTINCT type) as sensor_types
                FROM sensor_active
                """
            )
            stats["sensors"] = cur.fetchone()
        except Exception:
            stats["sensors_by_type"] = []
            stats["sensors"] = {
                "total_sensors": 0,
                "active_sensors": 0,
                "sensor_types": 0,
            }

        try:
            cur.execute(
                """
                SELECT COUNT(*) as count,
                       COUNT(CASE WHEN ti.occurred_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as last_30_days,
                       COUNT(CASE WHEN ti.occurred_at >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as last_7_days,
                       COALESCE(SUM(f.amount), 0) as total_fines
                FROM traffic_incident ti
                LEFT JOIN fine f ON ti.id = f.traffic_incident_id
                """
            )
            incident_summary = cur.fetchone()

            cur.execute(
                """
                SELECT ti.location, COUNT(*) as count,
                       COUNT(f.id) as fine_count,
                       COALESCE(AVG(f.amount), 0) as avg_fine
                FROM traffic_incident ti
                LEFT JOIN fine f ON ti.id = f.traffic_incident_id
                GROUP BY ti.location
                ORDER BY count DESC
                """
            )
            stats["incidents_by_location"] = cur.fetchall()

            stats["incidents"] = {
                "total_incidents": incident_summary.get("count", 0) if incident_summary else 0,
                "resolved": 0,
                "pending": incident_summary.get("count", 0) if incident_summary else 0,
                "last_30_days": incident_summary.get("last_30_days", 0) if incident_summary else 0,
                "last_7_days": incident_summary.get("last_7_days", 0) if incident_summary else 0,
                "total_fines": incident_summary.get("total_fines", 0) if incident_summary else 0,
            }
        except Exception:
            stats["incidents_by_location"] = []
            stats["incidents"] = {
                "total_incidents": 0,
                "resolved": 0,
                "pending": 0,
                "last_30_days": 0,
                "last_7_days": 0,
                "total_fines": 0,
            }

        try:
            cur.execute(
                """
                SELECT COUNT(*) as total_fines,
                       COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_fines,
                       COUNT(CASE WHEN status = 'overdue' THEN 1 END) as overdue_fines,
                       COUNT(CASE WHEN status = 'paid' THEN 1 END) as paid_fines,
                       COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_fines,
                       COALESCE(SUM(amount), 0) as total_amount,
                       COALESCE(SUM(CASE WHEN status = 'pending' THEN amount END), 0) as pending_amount,
                       COALESCE(SUM(CASE WHEN status = 'overdue' THEN amount END), 0) as overdue_amount,
                       COALESCE(SUM(CASE WHEN status = 'paid' THEN amount END), 0) as paid_amount,
                       COALESCE(AVG(amount), 0) as avg_amount
                FROM fine
                """
            )
            stats["fines"] = cur.fetchone()

            cur.execute(
                """
                SELECT status, COUNT(*) as count, COALESCE(SUM(amount), 0) as total_amount
                FROM fine
                GROUP BY status
                ORDER BY count DESC
                """
            )
            stats["fines_by_status"] = cur.fetchall()
        except Exception:
            stats["fines_by_status"] = []
            stats["fines"] = {
                "total_fines": 0,
                "pending_fines": 0,
                "overdue_fines": 0,
                "paid_fines": 0,
                "cancelled_fines": 0,
                "total_amount": 0,
                "pending_amount": 0,
                "overdue_amount": 0,
                "paid_amount": 0,
                "avg_amount": 0,
            }

        try:
            cur.execute(
                """
                SELECT DATE(timestamp) as date, COUNT(*) as readings_count
                FROM reading
                WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY DATE(timestamp)
                ORDER BY date
                """
            )
            stats["readings_last_7_days"] = cur.fetchall()
        except Exception:
            stats["readings_last_7_days"] = []

        return stats

    def update_statistics(self, stats):
        self._update_main_cards(stats)
        self._update_secondary_cards(stats)
        self._update_tables(stats)

    def _update_main_cards(self, stats):
        cards = [
            (
                "👤 Usuários",
                stats["users"]["total"],
                f"{stats['users']['this_month']} novos este mês",
                f"{stats['users']['this_week']} novos esta semana",
                self.colors["primary"],
            ),
            (
                "👥 Cidadãos",
                stats["citizens"]["total"],
                f"Com dívida: {stats['citizens']['with_debt']}",
                format_currency_brl(stats["citizens"]["total_debt"]),
                self.colors["success"],
            ),
            (
                "🚗 Veículos",
                stats["vehicles"]["total"],
                f"Ativos: {stats['vehicles']['active']}",
                f"Bloqueados: {stats['vehicles']['blocked']}",
                self.colors["warning"],
            ),
            (
                "⚠️ Incidentes",
                stats["incidents"]["total_incidents"],
                f"Últimos 7 dias: {stats['incidents']['last_7_days']}",
                f"Últimos 30 dias: {stats['incidents']['last_30_days']}",
                self.colors["accent"],
            ),
            (
                "💰 Multas",
                stats["fines"]["total_fines"],
                f"Pendentes: {stats['fines']['pending_fines']}",
                format_currency_brl(stats["fines"]["total_amount"]),
                self.colors["secondary"],
            ),
        ]

        while self.main_cards_layout.count():
            item = self.main_cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for i, (title, total, secondary, extra, color) in enumerate(cards):
            row = i // 3
            col = i % 3
            card = StatCard(title, total, secondary, extra, color, self.main_cards_container)
            self.main_cards_layout.addWidget(card, row, col)

    def _update_secondary_cards(self, stats):
        users_total = stats["users"]["total"]
        users_this_month = stats["users"]["this_month"]
        month_percent = (users_this_month / users_total * 100) if users_total > 0 else 0

        citizens_with_debt = stats["citizens"]["with_debt"]
        citizens_total = stats["citizens"]["total"]
        debt_percent = (citizens_with_debt / citizens_total * 100) if citizens_total > 0 else 0

        vehicles_total = stats["vehicles"]["total"]
        vehicles_blocked = stats["vehicles"]["blocked"]
        blocked_percent = (vehicles_blocked / vehicles_total * 100) if vehicles_total > 0 else 0

        incidents_total = stats["incidents"]["total_incidents"]
        incidents_resolved = stats["incidents"]["resolved"]
        resolved_percent = (incidents_resolved / incidents_total * 100) if incidents_total > 0 else 0

        secondary_cards = [
            (
                "👤 Usuários Totais",
                users_total,
                f"{month_percent:.1f}% novos este mês",
                self.colors["primary"],
            ),
            (
                "💳 Cidadãos c/ Dívida",
                citizens_with_debt,
                f"{debt_percent:.1f}% do total",
                self.colors["warning"],
            ),
            (
                "📹 Sensores",
                stats["sensors"]["total_sensors"],
                f"{stats['sensors']['active_sensors']} ativos",
                self.colors["secondary"],
            ),
            (
                "🔒 Veículos Bloqueados",
                vehicles_blocked,
                f"{blocked_percent:.1f}%",
                self.colors["warning"],
            ),
            (
                "💳 Multas Pendentes",
                stats["fines"]["pending_fines"],
                format_currency_brl(stats["fines"]["pending_amount"]),
                self.colors["accent"],
            ),
            (
                "⚠️ Multas Vencidas",
                stats["fines"]["overdue_fines"],
                format_currency_brl(stats["fines"]["overdue_amount"]),
                self.colors["warning"],
            ),
            (
                "✅ Incidentes Resolvidos",
                incidents_resolved,
                f"{resolved_percent:.1f}%",
                self.colors["success"],
            ),
        ]

        while self.secondary_cards_layout.count():
            item = self.secondary_cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for title, value, extra, color in secondary_cards:
            card = SummaryCard(title, value, extra, color, self.secondary_cards_container)
            self.secondary_cards_layout.addWidget(card)

        self.secondary_cards_layout.addStretch(1)

    def _update_tables(self, stats):
        status_map = {
            "pending": "Pendente",
            "overdue": "Vencida",
            "paid": "Paga",
            "cancelled": "Cancelada",
        }

        self._populate_table(
            self.sensors_table,
            stats.get("sensors_by_type", []),
            lambda row: [
                row.get("type") or "N/A",
                row.get("count") or 0,
                row.get("active") or 0,
            ],
        )

        self._populate_table(
            self.incidents_table,
            stats.get("incidents_by_location", []),
            lambda row: [
                row.get("location") or "N/A",
                row.get("count") or 0,
                row.get("fine_count") or 0,
                format_currency_brl(row.get("avg_fine") or 0),
            ],
        )

        self._populate_table(
            self.fines_table,
            stats.get("fines_by_status", []),
            lambda row: [
                status_map.get(row.get("status"), row.get("status") or "N/A"),
                row.get("count") or 0,
                format_currency_brl(row.get("total_amount") or 0),
            ],
        )

    def _populate_table(self, table, rows, mapper):
        table.setSortingEnabled(False)
        table.setRowCount(0)
        for row in rows:
            values = mapper(row)
            row_index = table.rowCount()
            table.insertRow(row_index)
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                table.setItem(row_index, col, item)
        table.setSortingEnabled(True)

    def export_statistics(self):
        if not self.app.connected:
            QMessageBox.warning(
                self,
                "Aviso",
                "Conecte-se ao banco de dados para exportar estatísticas!",
            )
            return

        default_name = f"estatisticas_smartcity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Estatísticas",
            os.path.join(os.getcwd(), default_name),
            "Arquivo Excel (*.xlsx);;Arquivo CSV (*.csv);;Todos os Arquivos (*.*)",
        )

        if not file_path:
            return

        if not file_path.lower().endswith((".xlsx", ".csv")):
            file_path += ".xlsx"

        is_excel = file_path.lower().endswith(".xlsx")

        try:
            conn_string = self.app.get_connection_string()
            with psy.connect(conn_string) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    stats = self._load_stats(cur)

            import pandas as pd

            export_data = [
                ["ESTATÍSTICAS GERAIS", "", ""],
                ["Métrica", "Total", "Descrição"],
                ["Total de Usuários", stats["users"]["total"], "Número total de usuários cadastrados"],
                ["Total de Cidadãos", stats["citizens"]["total"], "Número total de cidadãos cadastrados"],
                ["Total de Veículos", stats["vehicles"]["total"], "Número total de veículos cadastrados"],
                ["Total de Sensores", stats["sensors"]["total_sensors"], "Número total de sensores cadastrados"],
                ["Total de Incidentes", stats["incidents"]["total_incidents"], "Número total de incidentes registrados"],
                ["Total de Multas", stats["fines"]["total_fines"], "Número total de multas geradas"],
                ["", "", ""],
                ["ESTATÍSTICAS DE USUÁRIOS", "", ""],
                ["Métrica", "Total", "Descrição"],
                ["Usuários Ativos", stats["users"]["total"], "Usuários com acesso ao sistema"],
                ["Usuários Inativos", 0, "Usuários sem acesso (calculado)"],
                ["Novos Usuários (30 dias)", stats["users"]["this_month"], "Usuários cadastrados nos últimos 30 dias"],
                ["", "", ""],
                ["ESTATÍSTICAS DE CIDADÃOS", "", ""],
                ["Métrica", "Total", "Descrição"],
                ["Cidadãos Ativos", stats["citizens"]["with_access"], "Cidadãos com permissão de acesso"],
                [
                    "Cidadãos Inativos",
                    stats["citizens"]["total"] - stats["citizens"]["with_access"],
                    "Cidadãos sem permissão de acesso",
                ],
                ["Saldo Total (R$)", 0.00, "Saldo total disponível dos cidadãos"],
                ["Dívida Total (R$)", float(stats["citizens"]["total_debt"]), "Dívida total acumulada dos cidadãos"],
                ["Novos Cidadãos (30 dias)", 0, "Cidadãos cadastrados nos últimos 30 dias"],
                ["", "", ""],
                ["ESTATÍSTICAS DE VEÍCULOS", "", ""],
                ["Métrica", "Total", "Descrição"],
                ["Veículos Ativos", stats["vehicles"]["active"], "Veículos com permissão de circulação"],
                ["Veículos Inativos", stats["vehicles"]["blocked"], "Veículos sem permissão de circulação"],
                ["Novos Veículos (30 dias)", 0, "Veículos cadastrados nos últimos 30 dias"],
                ["", "", ""],
                ["ESTATÍSTICAS DE SENSORES", "", ""],
                ["Métrica", "Total", "Descrição"],
                ["Sensores Ativos", stats["sensors"]["active_sensors"], "Sensores atualmente em operação"],
                [
                    "Sensores Inativos",
                    stats["sensors"]["total_sensors"] - stats["sensors"]["active_sensors"],
                    "Sensores desativados",
                ],
                ["Sensores com Leituras", 0, "Sensores que já registraram leituras"],
                ["Novos Sensores (30 dias)", 0, "Sensores cadastrados nos últimos 30 dias"],
                ["", "", ""],
                ["ESTATÍSTICAS DE INCIDENTES", "", ""],
                ["Métrica", "Total", "Descrição"],
                ["Incidentes (7 dias)", stats["incidents"]["last_7_days"], "Incidentes registrados nos últimos 7 dias"],
                ["Incidentes (30 dias)", stats["incidents"]["last_30_days"], "Incidentes registrados nos últimos 30 dias"],
                ["", "", ""],
                ["ESTATÍSTICAS DE MULTAS", "", ""],
                ["Métrica", "Total", "Descrição"],
                ["Multas Pendentes", stats["fines"]["pending_fines"], "Multas aguardando pagamento"],
                ["Multas Pagas", stats["fines"]["paid_fines"], "Multas já quitadas"],
                ["Multas Canceladas", stats["fines"]["cancelled_fines"], "Multas canceladas"],
                ["Multas Vencidas", stats["fines"]["overdue_fines"], "Multas com vencimento ultrapassado"],
                [
                    "Valor Total Pendente (R$)",
                    float(stats["fines"]["pending_amount"]),
                    "Valor total das multas pendentes",
                ],
                ["Valor Total Pago (R$)", float(stats["fines"]["paid_amount"]), "Valor total das multas já pagas"],
                [
                    "Valor Total Vencido (R$)",
                    float(stats["fines"]["overdue_amount"]),
                    "Valor total das multas vencidas",
                ],
                ["", "", ""],
                ["RESUMO FINANCEIRO", "", ""],
                ["Métrica", "Valor (R$)", "Descrição"],
                ["Saldo Total dos Cidadãos", 0.00, "Saldo total disponível dos cidadãos"],
                [
                    "Dívida Total dos Cidadãos",
                    float(stats["citizens"]["total_debt"]),
                    "Dívida total acumulada dos cidadãos",
                ],
                [
                    "Valor Total de Multas Pendentes",
                    float(stats["fines"]["pending_amount"]),
                    "Valor total das multas pendentes",
                ],
                [
                    "Valor Total de Multas Pagas",
                    float(stats["fines"]["paid_amount"]),
                    "Valor total das multas já pagas",
                ],
                [
                    "Valor Total de Multas Vencidas",
                    float(stats["fines"]["overdue_amount"]),
                    "Valor total das multas vencidas",
                ],
            ]

            df = pd.DataFrame(export_data, columns=["Categoria", "Valor", "Descrição"])

            if is_excel:
                with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                    df.to_excel(writer, sheet_name="Estatísticas", index=False)

                    metadata_df = pd.DataFrame(
                        [
                            ["SmartCityOS - Sistema Operacional Inteligente para Cidades"],
                            [f"Data da Exportação: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"],
                            ["Formato: Excel (.xlsx)"],
                            ["Versão: 1.0"],
                        ],
                        columns=["Informação"],
                    )
                    metadata_df.to_excel(writer, sheet_name="Metadados", index=False)

                QMessageBox.information(
                    self,
                    "Sucesso",
                    f"Estatísticas exportadas com sucesso!\n\nArquivo Excel salvo em:\n{file_path}",
                )
            else:
                df.to_csv(file_path, index=False, encoding="utf-8-sig")
                QMessageBox.information(
                    self,
                    "Sucesso",
                    f"Estatísticas exportadas com sucesso!\n\nArquivo CSV salvo em:\n{file_path}",
                )

        except ImportError:
            QMessageBox.critical(
                self,
                "Erro",
                "Bibliotecas necessárias não encontradas!\n\nInstale:\npip install pandas openpyxl",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar estatísticas: {exc}")


class SQLPage(QWidget):
    """Página do Console SQL."""

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.colors = app.colors
        self.last_query = ""

        self.examples = [
            "SELECT COUNT(*) as total_citizens FROM citizen_active;",
            "SELECT * FROM vehicle_active WHERE allowed = TRUE;",
            "SELECT v.license_plate, c.first_name FROM vehicle_active v JOIN citizen_active c ON v.citizen_id = c.id;",
            "SELECT status, COUNT(*) FROM fine GROUP BY status;",
            "SELECT type, COUNT(*) FROM sensor_active GROUP BY type ORDER BY COUNT DESC;",
            "SELECT username, created_at FROM app_user_active ORDER BY created_at DESC LIMIT 5;",
            "SELECT * FROM citizen_active WHERE debt > 0 ORDER BY debt DESC;",
            "SELECT s.type, s.location, COUNT(r.id) as readings FROM sensor_active s LEFT JOIN reading r ON s.id = r.sensor_id GROUP BY s.id, s.type, s.location ORDER BY readings DESC;",
        ]
        self.default_sql = "-- Digite sua consulta SQL aqui\nSELECT * FROM app_user_active LIMIT 10;"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QFrame(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(12)

        title_label = QLabel("🔍 Console SQL", header)
        title_label.setStyleSheet("font-size: 16px; font-weight: 700;")

        controls_widget = QWidget(header)
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)

        self.clear_button = QPushButton("🗑️ Limpar", controls_widget)
        self.clear_button.setObjectName("DangerButton")
        self.clear_button.clicked.connect(self.clear_sql)

        self.export_button = QPushButton("📊 Exportar", controls_widget)
        self.export_button.setObjectName("SuccessButton")
        self.export_button.clicked.connect(self.export_sql_results)

        self.example_button = QPushButton("📋 Exemplo", controls_widget)
        self.example_button.setObjectName("PrimaryButton")
        self.example_button.clicked.connect(self.load_sql_example)

        controls_layout.addWidget(self.clear_button)
        controls_layout.addWidget(self.export_button)
        controls_layout.addWidget(self.example_button)

        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(controls_widget)

        self.message_label = QLabel(
            "Conecte-se ao banco de dados para utilizar o console SQL.",
            self,
        )
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet("color: #696969; font-size: 12px;")

        self.content_container = QWidget(self)
        content_layout = QHBoxLayout(self.content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        editor_group = QGroupBox("Editor SQL", self.content_container)
        editor_group.setProperty("role", "sql_group")
        editor_layout = QVBoxLayout(editor_group)
        editor_layout.setContentsMargins(12, 12, 12, 12)
        editor_layout.setSpacing(10)

        self.sql_text = QTextEdit(editor_group)
        self.sql_text.setObjectName("SqlEditor")
        self.sql_text.setFont(QFont("Consolas", 11))

        self.run_button = QPushButton("▶️ Executar Query", editor_group)
        self.run_button.setObjectName("SuccessButton")
        self.run_button.clicked.connect(self.execute_sql)

        editor_layout.addWidget(self.sql_text, 1)
        editor_layout.addWidget(self.run_button, 0, Qt.AlignLeft)

        results_group = QGroupBox("Resultados da Consulta", self.content_container)
        results_group.setProperty("role", "sql_group")
        results_layout = QVBoxLayout(results_group)
        results_layout.setContentsMargins(12, 12, 12, 12)
        results_layout.setSpacing(10)

        self.results_table = QTableWidget(results_group)
        self.results_table.setColumnCount(0)
        self.results_table.setRowCount(0)
        self.results_table.setSortingEnabled(True)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setStretchLastSection(True)

        self.results_info = QLabel(
            "Execute uma query para ver os resultados",
            results_group,
        )
        self.results_info.setStyleSheet("color: #696969; font-size: 11px;")

        results_layout.addWidget(self.results_table, 1)
        results_layout.addWidget(self.results_info)

        content_layout.addWidget(editor_group, 1)
        content_layout.addWidget(results_group, 1)

        layout.addWidget(header)
        layout.addWidget(self.message_label)
        layout.addWidget(self.content_container, 1)

        self.set_connected(False)
        self.clear_sql()

    def set_connected(self, connected):
        self.message_label.setVisible(not connected)
        self.content_container.setVisible(connected)
        self.run_button.setEnabled(connected)
        self.export_button.setEnabled(connected)

    def load_console(self):
        if not self.app.connected:
            self.set_connected(False)
            return

        self.set_connected(True)
        if not self.sql_text.toPlainText().strip():
            self.clear_sql()
        self.sql_text.setFocus()

    def clear_sql(self):
        self.sql_text.setPlainText(self.default_sql)
        cursor = self.sql_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.sql_text.setTextCursor(cursor)

        self.results_table.setRowCount(0)
        self.results_table.setColumnCount(0)
        self.results_info.setText("Execute uma query para ver os resultados")
        self.last_query = ""

    def load_sql_example(self):
        example = choice(self.examples)
        self.sql_text.setPlainText(example)
        cursor = self.sql_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.sql_text.setTextCursor(cursor)
        self.sql_text.setFocus()

    def execute_sql(self):
        if not self.app.connected:
            QMessageBox.warning(self, "Aviso", "Conecte-se ao banco de dados primeiro!")
            return

        sql = self.sql_text.toPlainText().strip()
        valid, title, message, level = self._validate_sql(sql)
        if not valid:
            if level == "warning":
                QMessageBox.warning(self, title, message)
            else:
                QMessageBox.critical(self, title, message)
            return

        try:
            conn_string = self.app.get_connection_string()
            with psy.connect(conn_string) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(sql)
                    results = cur.fetchall()
                    columns = [desc.name for desc in cur.description] if cur.description else []

            self._update_results_table(columns, results)
            if results:
                self.results_info.setText(f"✅ {len(results)} registros encontrados")
            else:
                self.results_info.setText("📭 Nenhum registro encontrado")

            self.last_query = sql
            self.app.status_label.setText("Consulta SQL executada")
        except psy.Error as exc:
            self._update_results_table([], [])
            self.results_info.setText(f"❌ Erro SQL: {exc}")
            QMessageBox.critical(self, "Erro SQL", f"Erro ao executar consulta:\n{exc}")
        except Exception as exc:
            self._update_results_table([], [])
            self.results_info.setText(f"❌ Erro: {exc}")
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao executar consulta: {exc}",
            )

    def export_sql_results(self):
        if not self.app.connected:
            QMessageBox.warning(self, "Aviso", "Conecte-se ao banco de dados primeiro!")
            return

        sql = self.sql_text.toPlainText().strip()
        valid, title, message, level = self._validate_sql(sql)
        if not valid:
            if level == "warning":
                QMessageBox.warning(self, title, message)
            else:
                QMessageBox.critical(self, title, message)
            return

        default_name = f"resultados_sql_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Resultados SQL",
            os.path.join(os.getcwd(), default_name),
            "Arquivo Excel (*.xlsx);;Arquivo CSV (*.csv);;Todos os Arquivos (*.*)",
        )

        if not file_path:
            return

        if not file_path.lower().endswith((".xlsx", ".csv")):
            file_path += ".xlsx"

        is_excel = file_path.lower().endswith(".xlsx")

        try:
            conn_string = self.app.get_connection_string()
            with psy.connect(conn_string) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(sql)
                    results = cur.fetchall()

            if not results:
                QMessageBox.warning(
                    self,
                    "Sem Resultados",
                    "A consulta não retornou nenhum resultado!",
                )
                return

            import pandas as pd

            df = pd.DataFrame(results)

            if is_excel:
                with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                    df.to_excel(writer, sheet_name="Resultados", index=False)

                    query_info = pd.DataFrame(
                        [
                            ["SmartCityOS - Resultados de Consulta SQL"],
                            [f"Data da Exportação: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"],
                            ["Formato: Excel (.xlsx)"],
                            ["Consulta SQL:"],
                            [sql],
                            [f"Total de Registros: {len(results)}"],
                        ],
                        columns=["Informação"],
                    )
                    query_info.to_excel(writer, sheet_name="Informações", index=False)

                QMessageBox.information(
                    self,
                    "Sucesso",
                    f"Resultados exportados com sucesso!\n\nArquivo Excel salvo em:\n{file_path}",
                )
            else:
                df.to_csv(file_path, index=False, encoding="utf-8-sig")
                QMessageBox.information(
                    self,
                    "Sucesso",
                    f"Resultados exportados com sucesso!\n\nArquivo CSV salvo em:\n{file_path}",
                )
        except ImportError:
            QMessageBox.critical(
                self,
                "Erro",
                "Bibliotecas necessárias não encontradas!\n\nInstale:\npip install pandas openpyxl",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar resultados: {exc}")

    def _update_results_table(self, columns, results):
        self.results_table.setSortingEnabled(False)
        self.results_table.setColumnCount(len(columns))
        self.results_table.setRowCount(0)

        if columns:
            headers = [col.replace("_", " ").title() for col in columns]
            self.results_table.setHorizontalHeaderLabels(headers)

        for row in results:
            row_index = self.results_table.rowCount()
            self.results_table.insertRow(row_index)
            for col_index, col in enumerate(columns):
                value = row.get(col, "")
                display_value = "NULL" if value is None else str(value)
                item = QTableWidgetItem(display_value)
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.results_table.setItem(row_index, col_index, item)

        self.results_table.setSortingEnabled(True)

    def _validate_sql(self, sql):
        if not sql:
            return False, "Aviso", "Digite uma consulta SQL!", "warning"

        lines = sql.split("\n")
        first_non_comment_line = None
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("--"):
                first_non_comment_line = stripped
                break

        if not first_non_comment_line:
            return False, "Aviso", "Digite uma consulta SQL válida!", "warning"

        sql_upper = sql.upper()
        forbidden_commands = [
            "ALTER",
            "DROP",
            "UPDATE",
            "DELETE",
            "INSERT",
            "CREATE",
            "TRUNCATE",
            "GRANT",
            "REVOKE",
        ]

        for cmd in forbidden_commands:
            pattern = r"\b" + cmd + r"\b"
            if re.search(pattern, sql_upper):
                return (
                    False,
                    "Erro",
                    f"Comando '{cmd}' não é permitido no console SQL!\n\nApenas consultas SELECT são permitidas.",
                    "error",
                )

        first_line_upper = first_non_comment_line.upper()
        if not (first_line_upper.startswith("SELECT") or first_line_upper.startswith("WITH")):
            return (
                False,
                "Erro",
                "Apenas consultas SELECT são permitidas no console SQL!\n\nUse SELECT para consultar dados.",
                "error",
            )

        restricted_tables = {
            "citizen": "citizen_active",
            "vehicle": "vehicle_active",
            "sensor": "sensor_active",
            "app_user": "app_user_active",
        }

        for table, view in restricted_tables.items():
            patterns = [
                rf"\bFROM\s+{table}\b(?!\s*\()",
                rf"\bJOIN\s+{table}\b(?!\s*\()",
                rf"\b{table}\s+AS\b",
                rf"\b{table}\s+\w+\s*,",
            ]

            for pattern in patterns:
                if re.search(pattern, sql, re.IGNORECASE):
                    return (
                        False,
                        "Erro de Acesso Restrito",
                        f"❌ Tabela '{table}' não pode ser consultada diretamente!\n\n"
                        f"📋 Use a view '{view}' em vez da tabela base.\n\n"
                        f"🔒 Esta restrição garante que dados soft-deletados não sejam exibidos.\n\n"
                        f"✅ Exemplo correto: SELECT * FROM {view};",
                        "error",
                    )

        return True, "", "", ""


class SettingsPage(QWidget):
    """Página de Configurações do Sistema."""

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.colors = app.colors
        self.settings_path = os.path.join(ROOT_DIR, "settings.json")
        self.setObjectName("SettingsPage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QFrame(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(12)

        title_label = QLabel("⚙️ Configurações do Sistema", header)
        title_label.setStyleSheet("font-size: 16px; font-weight: 700;")

        self.save_button = QPushButton("💾 Salvar Configurações", header)
        self.save_button.setObjectName("SuccessButton")
        self.save_button.clicked.connect(self.save_settings)

        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.save_button)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        content = QWidget(self.scroll_area)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(14)

        self.ui_group = QGroupBox("🎨 Preferências da Interface", content)
        self.ui_group.setProperty("role", "settings_group")
        ui_layout = QFormLayout(self.ui_group)
        ui_layout.setLabelAlignment(Qt.AlignLeft)

        self.theme_combo = QComboBox(self.ui_group)
        self.theme_combo.addItems(["Escuro", "Claro", "Azul"])
        ui_layout.addRow("Tema:", self.theme_combo)

        self.language_combo = QComboBox(self.ui_group)
        self.language_combo.addItems(["Português", "English", "Español"])
        ui_layout.addRow("Idioma:", self.language_combo)

        self.system_group = QGroupBox("🔧 Configurações do Sistema", content)
        self.system_group.setProperty("role", "settings_group")
        system_layout = QVBoxLayout(self.system_group)
        system_layout.setContentsMargins(12, 12, 12, 12)
        system_layout.setSpacing(8)

        self.autosave_check = QCheckBox("Auto-save automático", self.system_group)
        self.notifications_check = QCheckBox("Habilitar notificações", self.system_group)

        system_layout.addWidget(self.autosave_check)
        system_layout.addWidget(self.notifications_check)

        self.database_group = QGroupBox("🗄️ Configurações do Banco de Dados", content)
        self.database_group.setProperty("role", "settings_group")
        db_layout = QFormLayout(self.database_group)
        db_layout.setLabelAlignment(Qt.AlignLeft)

        self.db_host_input = QLineEdit(self.database_group)
        self.db_port_input = QLineEdit(self.database_group)
        self.db_name_input = QLineEdit(self.database_group)

        self.db_host_input.setPlaceholderText("localhost")
        self.db_port_input.setPlaceholderText("5432")
        self.db_name_input.setPlaceholderText("smart_city_os")

        db_layout.addRow("Host:", self.db_host_input)
        db_layout.addRow("Porta:", self.db_port_input)
        db_layout.addRow("Database:", self.db_name_input)

        self.backup_group = QGroupBox("💾 Backup e Restauração", content)
        self.backup_group.setProperty("role", "settings_group")
        backup_layout = QVBoxLayout(self.backup_group)
        backup_layout.setContentsMargins(12, 12, 12, 12)
        backup_layout.setSpacing(8)

        self.connection_label = QLabel("🔴 Banco desconectado", self.backup_group)
        self.connection_label.setStyleSheet("color: #696969;")

        backup_buttons = QHBoxLayout()
        backup_buttons.setSpacing(8)

        self.backup_button = QPushButton("📦 Fazer Backup", self.backup_group)
        self.backup_button.setObjectName("PrimaryButton")
        self.backup_button.clicked.connect(self.backup_database)

        self.restore_button = QPushButton("📂 Restaurar Backup", self.backup_group)
        self.restore_button.setObjectName("WarningButton")
        self.restore_button.clicked.connect(self.restore_database)

        backup_buttons.addWidget(self.backup_button)
        backup_buttons.addWidget(self.restore_button)
        backup_buttons.addStretch(1)

        backup_layout.addWidget(self.connection_label)
        backup_layout.addLayout(backup_buttons)

        self.info_group = QGroupBox("ℹ️ Informações do Sistema", content)
        self.info_group.setProperty("role", "settings_group")
        info_layout = QVBoxLayout(self.info_group)
        info_layout.setContentsMargins(12, 12, 12, 12)

        self.info_label = QLabel("", self.info_group)
        self.info_label.setStyleSheet("color: #696969; font-size: 11px;")
        self.info_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        info_layout.addWidget(self.info_label)

        content_layout.addWidget(self.ui_group)
        content_layout.addWidget(self.system_group)
        content_layout.addWidget(self.database_group)
        content_layout.addWidget(self.backup_group)
        content_layout.addWidget(self.info_group)
        content_layout.addStretch(1)

        self.scroll_area.setWidget(content)

        layout.addWidget(header)
        layout.addWidget(self.scroll_area, 1)

        self.load_settings()
        self.update_connection_state(self.app.connected)

    def update_connection_state(self, connected):
        if connected:
            self.connection_label.setText("🟢 Banco conectado")
        else:
            self.connection_label.setText("🔴 Banco desconectado")

        self.backup_button.setEnabled(connected)
        self.restore_button.setEnabled(connected)
        self.refresh_system_info()

    def refresh_system_info(self):
        python_version = sys.version.split()[0]
        pg_version = "Desconectado"
        if self.app.connected:
            try:
                conn_string = self.app.get_connection_string()
                with psy.connect(conn_string) as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT version()")
                        version = cur.fetchone()
                        if version:
                            pg_version = version[0].split(",")[0]
            except Exception:
                pg_version = "Desconectado"

        info_text = (
            "Versão: SmartCityOS v1.0.0\n"
            f"Python: {python_version}\n"
            f"PostgreSQL: {pg_version}\n"
            f"Último acesso: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )
        self.info_label.setText(info_text)

    def load_settings(self):
        defaults = {
            "database": {
                "host": "localhost",
                "port": "5432",
                "dbname": "smart_city_os",
            },
            "ui": {"theme": "Escuro", "language": "Português"},
            "system": {"autosave": True, "notifications": True},
        }

        settings = defaults
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
            except Exception:
                settings = defaults

        db_config = settings.get("database", defaults["database"])
        ui_config = settings.get("ui", defaults["ui"])
        system_config = settings.get("system", defaults["system"])

        env_host = os.getenv("DB_HOST")
        env_port = os.getenv("DB_PORT")
        env_name = os.getenv("DB_NAME")

        host_value = db_config.get("host") or env_host or defaults["database"]["host"]
        port_value = db_config.get("port") or env_port or defaults["database"]["port"]
        name_value = db_config.get("dbname") or env_name or defaults["database"]["dbname"]

        self.db_host_input.setText(host_value)
        self.db_port_input.setText(port_value)
        self.db_name_input.setText(name_value)

        theme = ui_config.get("theme", defaults["ui"]["theme"])
        language = ui_config.get("language", defaults["ui"]["language"])
        if theme in [self.theme_combo.itemText(i) for i in range(self.theme_combo.count())]:
            self.theme_combo.setCurrentText(theme)
        if language in [self.language_combo.itemText(i) for i in range(self.language_combo.count())]:
            self.language_combo.setCurrentText(language)

        self.autosave_check.setChecked(system_config.get("autosave", True))
        self.notifications_check.setChecked(system_config.get("notifications", True))

        self.refresh_system_info()

    def save_settings(self):
        settings = {
            "database": {
                "host": self.db_host_input.text().strip(),
                "port": self.db_port_input.text().strip(),
                "dbname": self.db_name_input.text().strip(),
            },
            "ui": {
                "theme": self.theme_combo.currentText(),
                "language": self.language_combo.currentText(),
            },
            "system": {
                "autosave": self.autosave_check.isChecked(),
                "notifications": self.notifications_check.isChecked(),
            },
        }

        try:
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

            self._sync_env(settings.get("database", {}))

            QMessageBox.information(
                self,
                "Sucesso",
                "✅ Configurações salvas com sucesso!\n\n"
                "Se estiver conectado ao banco, desconecte e conecte novamente para aplicar mudanças.",
            )
            self.app.status_label.setText("Configurações salvas")
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"❌ Erro ao salvar configurações: {exc}")

    def backup_database(self):
        if not self.app.connected:
            QMessageBox.warning(self, "Aviso", "Conecte-se ao banco de dados primeiro!")
            return

        default_name = f"backup_smartcity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        backup_file, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Backup",
            os.path.join(os.getcwd(), default_name),
            "Arquivos SQL (*.sql);;Todos os Arquivos (*.*)",
        )

        if not backup_file:
            return

        if not backup_file.lower().endswith(".sql"):
            backup_file += ".sql"

        try:
            conn_string = self.app.get_connection_string()
            with psy.connect(conn_string) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_type = 'BASE TABLE'
                        ORDER BY table_name
                        """
                    )
                    tables = [row[0] for row in cur.fetchall()]

                    with open(backup_file, "w", encoding="utf-8") as f:
                        f.write("-- SmartCityOS Database Backup\n")
                        f.write(f"-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"-- Database: {self.db_name_input.text().strip() or 'smart_city_os'}\n")
                        f.write(f"-- Total tables: {len(tables)}\n\n")

                        for table in tables:
                            f.write(f"--\n-- Data for table: {table}\n--\n\n")

                            cur.execute(sql.SQL("SELECT * FROM {}").format(sql.Identifier(table)))
                            rows = cur.fetchall()
                            columns = [desc.name for desc in cur.description] if cur.description else []

                            if not columns:
                                f.write(f"-- Table {table} has no columns\n\n")
                                continue

                            if rows:
                                col_list = ", ".join([self._quote_ident(col) for col in columns])
                                for row in rows:
                                    values = [self._format_sql_value(value) for value in row]
                                    insert_sql = (
                                        f"INSERT INTO {self._quote_ident(table)} "
                                        f"({col_list}) VALUES ({', '.join(values)});"
                                    )
                                    f.write(insert_sql + "\n")
                                f.write(f"\n-- {len(rows)} rows backed up for table {table}\n\n")
                            else:
                                f.write(f"-- Table {table} is empty\n\n")

            QMessageBox.information(
                self,
                "Backup",
                f"✅ Backup concluído com sucesso!\n\nArquivo: {backup_file}\n\nTabelas backup: {len(tables)}",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"❌ Erro ao fazer backup: {exc}")

    def restore_database(self):
        if not self.app.connected:
            QMessageBox.warning(self, "Aviso", "Conecte-se ao banco de dados primeiro!")
            return

        backup_file, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Arquivo de Backup",
            os.getcwd(),
            "Arquivos SQL (*.sql);;Todos os Arquivos (*.*)",
        )

        if not backup_file:
            return

        confirm = QMessageBox.question(
            self,
            "Confirmar Restauração",
            "⚠️ ATENÇÃO: Esta operação irá substituir todos os dados atuais!\n\nDeseja continuar?",
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            with open(backup_file, "r", encoding="utf-8") as f:
                sql_content = f.read()

            sql_commands = self._split_sql_commands(sql_content)

            conn_string = self.app.get_connection_string()
            with psy.connect(conn_string) as conn:
                conn.autocommit = True
                with conn.cursor() as cur:
                    success_count = 0
                    error_count = 0
                    errors = []

                    for i, command in enumerate(sql_commands):
                        if not command.strip():
                            continue

                        try:
                            cur.execute(command)
                            success_count += 1
                        except Exception as cmd_error:
                            error_count += 1
                            errors.append(f"Comando {i + 1}: {cmd_error}")
                            continue

            result_msg = (
                "✅ Restauração concluída!\n\n"
                f"Comandos executados com sucesso: {success_count}\n"
                f"Comandos com erro: {error_count}\n"
                f"Arquivo: {backup_file}"
            )

            if errors and len(errors) <= 5:
                result_msg += "\n\nErros encontrados:\n" + "\n".join(errors[:5])
            elif errors:
                result_msg += f"\n\nErros encontrados: {len(errors)} (primeiros 5 mostrados)"
                result_msg += "\n" + "\n".join(errors[:5])

            if error_count == 0:
                QMessageBox.information(
                    self,
                    "Restauração",
                    result_msg + "\n\n🎉 Todos os dados foram restaurados com sucesso!",
                )
            else:
                QMessageBox.warning(
                    self,
                    "Restauração",
                    result_msg + "\n\n⚠️ Alguns comandos falharam, mas a restauração foi concluída.",
                )
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"❌ Erro ao restaurar: {exc}")

    def _split_sql_commands(self, sql_content):
        commands = []
        current_command = ""

        for line in sql_content.split("\n"):
            line = line.strip()

            if line.startswith("--") or not line:
                continue

            current_command += line + " "

            if line.endswith(";"):
                commands.append(current_command.strip())
                current_command = ""

        if current_command.strip():
            commands.append(current_command.strip())

        return commands

    def _quote_ident(self, value):
        return '"' + str(value).replace('"', '""') + '"'

    def _format_sql_value(self, value):
        if value is None:
            return "NULL"
        if isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, datetime):
            return f"'{value.isoformat(sep=' ')}'"
        if isinstance(value, dict):
            return "'" + json.dumps(value).replace("'", "''") + "'"
        return "'" + str(value).replace("'", "''") + "'"

    def _sync_env(self, db_settings):
        updates = {}
        host = (db_settings.get("host") or "").strip()
        port = (db_settings.get("port") or "").strip()
        dbname = (db_settings.get("dbname") or "").strip()

        if host:
            updates["DB_HOST"] = host
        if port:
            updates["DB_PORT"] = port
        if dbname:
            updates["DB_NAME"] = dbname

        if not updates:
            return

        for key, value in updates.items():
            os.environ[key] = value

        try:
            self._update_env_file(updates)
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Aviso",
                f"Configurações salvas, mas não foi possível atualizar o arquivo .env.\n\n{exc}",
            )

    def _update_env_file(self, updates):
        env_path = os.path.join(ROOT_DIR, ".env")
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

        updated = set()
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                new_lines.append(line)
                continue

            prefix = ""
            normalized = stripped
            if stripped.startswith("export "):
                prefix = "export "
                normalized = stripped[7:]

            key = normalized.split("=", 1)[0].strip()
            if key in updates:
                new_lines.append(f"{prefix}{key}={updates[key]}\n")
                updated.add(key)
            else:
                new_lines.append(line)

        for key, value in updates.items():
            if key not in updated:
                new_lines.append(f"{key}={value}\n")

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)


class SmartCityOSQtApp(QMainWindow):
    """Janela principal do SmartCityOS em PySide6."""

    def __init__(self):
        super().__init__()
        load_dotenv()

        self.colors = {
            "primary": "#2E8B57",
            "secondary": "#4682B4",
            "accent": "#DC143C",
            "success": "#228B22",
            "warning": "#FF8C00",
            "danger": "#DC143C",
            "light": "#DBDBDB",
            "dark": "#2F4F4F",
            "white": "#FFFFFF",
            "black": "#000000",
            "background": "#F0F0F0",
            "card": "#FFFFFF",
            "border": "#D3D3D3",
            "text_primary": "#2F4F4F",
            "text_secondary": "#696969",
        }

        self.fonts = {
            "title": QFont("Segoe UI", 16, QFont.Bold),
            "heading": QFont("Segoe UI", 12, QFont.Bold),
            "normal": QFont("Segoe UI", 10),
            "small": QFont("Segoe UI", 9),
            "button": QFont("Segoe UI", 10, QFont.Bold),
        }

        self.connected = False

        self.setWindowTitle("SmartCityOS - Sistema Operacional Inteligente para Cidades")
        self.setMinimumSize(1200, 800)

        self._build_ui()
        self._apply_styles()
        self._start_clock()

    def _build_ui(self):
        central = QWidget(self)
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(10, 10, 10, 10)
        central_layout.setSpacing(8)

        header = self._build_header()
        body = self._build_body()
        status_bar = self._build_status_bar()

        central_layout.addWidget(header)
        central_layout.addWidget(body)
        central_layout.addWidget(status_bar)

        self.setCentralWidget(central)

    def _build_header(self):
        header = QFrame(self)
        header.setObjectName("Header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 12, 20, 12)

        left = QWidget(header)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)

        logo = QLabel("🏙️", left)
        logo.setFont(QFont("Segoe UI", 28))

        title = QLabel("SmartCityOS", left)
        title.setFont(self.fonts["title"])
        title.setStyleSheet(f"color: {self.colors['white']};")

        subtitle = QLabel("Sistema Operacional Inteligente para Cidades", left)
        subtitle.setFont(self.fonts["normal"])
        subtitle.setStyleSheet(f"color: {self.colors['light']};")

        left_layout.addWidget(logo)
        left_layout.addWidget(title)
        left_layout.addWidget(subtitle)

        right = QWidget(header)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        status_row = QHBoxLayout()
        self.connection_status = QLabel("🔴 Desconectado", right)
        self.connection_status.setFont(self.fonts["normal"])
        self.connection_status.setStyleSheet(f"color: {self.colors['light']};")

        self.connect_button = QPushButton("🔌 Conectar", right)
        self.connect_button.setObjectName("PrimaryButton")
        self.connect_button.setFont(self.fonts["button"])
        self.connect_button.clicked.connect(self.toggle_connection)

        status_row.addWidget(self.connection_status)
        status_row.addWidget(self.connect_button)

        info_row = QHBoxLayout()
        version_label = QLabel("v1.0.0", right)
        version_label.setStyleSheet(f"color: {self.colors['light']};")
        info_row.addWidget(version_label)

        right_layout.addLayout(status_row)
        right_layout.addLayout(info_row)

        header_layout.addWidget(left)
        header_layout.addStretch(1)
        header_layout.addWidget(right)

        return header

    def _build_body(self):
        body = QWidget(self)
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(10)

        self.sidebar = self._build_sidebar()
        self.stack = QStackedWidget(body)

        body_layout.addWidget(self.sidebar)
        body_layout.addWidget(self.stack, 1)

        self._build_pages()

        return body

    def _build_sidebar(self):
        sidebar = QFrame(self)
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(260)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        title = QLabel("📋 Menu Principal", sidebar)
        title.setFont(self.fonts["heading"])
        title.setStyleSheet(f"color: {self.colors['text_primary']};")

        separator = QFrame(sidebar)
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(f"color: {self.colors['border']};")

        layout.addWidget(title)
        layout.addWidget(separator)

        self.nav_buttons = {}
        buttons_data = [
            ("Dashboard", "📊 Dashboard"),
            ("Cidadãos", "👥 Cidadãos"),
            ("Veículos", "🚗 Veículos"),
            ("Sensores", "📹 Sensores"),
            ("Incidentes", "⚠️ Incidentes"),
            ("Multas", "💰 Multas"),
            ("Estatísticas", "📈 Estatísticas"),
            ("SQL", "🔍 Consultas SQL"),
            ("Configurações", "⚙️ Configurações"),
        ]

        for key, label in buttons_data:
            button = QPushButton(label, sidebar)
            button.setObjectName("SidebarButton")
            button.setFont(self.fonts["normal"])
            button.clicked.connect(lambda _, name=key: self.navigate(name))
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            layout.addWidget(button)
            self.nav_buttons[key] = button

        layout.addStretch(1)
        return sidebar

    def _build_pages(self):
        self.pages = {}

        self.dashboard_page = DashboardPage(self.refresh_dashboard, self)
        self._add_page("Dashboard", self.dashboard_page)

        self.citizens_page = CitizensPage(self, self)
        self._add_page("Cidadãos", self.citizens_page)

        self.vehicles_page = VehiclesPage(self, self)
        self._add_page("Veículos", self.vehicles_page)

        self.sensors_page = SensorsPage(self, self)
        self._add_page("Sensores", self.sensors_page)

        self.incidents_page = IncidentsPage(self, self)
        self._add_page("Incidentes", self.incidents_page)

        self.fines_page = FinesPage(self, self)
        self._add_page("Multas", self.fines_page)

        self.statistics_page = StatisticsPage(self, self)
        self._add_page("Estatísticas", self.statistics_page)

        self.sql_page = SQLPage(self, self)
        self._add_page("SQL", self.sql_page)

        self.settings_page = SettingsPage(self, self)
        self._add_page("Configurações", self.settings_page)

        placeholders = {
        }

        for key, desc in placeholders.items():
            page = PlaceholderPage(f"{key}", desc, self)
            self._add_page(key, page)

        self.navigate("Dashboard")

    def _add_page(self, name, widget):
        self.pages[name] = widget
        self.stack.addWidget(widget)

    def _build_status_bar(self):
        status = QFrame(self)
        status.setObjectName("StatusBar")
        layout = QHBoxLayout(status)
        layout.setContentsMargins(12, 6, 12, 6)

        self.status_label = QLabel("Pronto", status)
        self.status_label.setStyleSheet("color: #2F4F4F;")

        self.datetime_label = QLabel("", status)
        self.datetime_label.setStyleSheet("color: #696969;")

        layout.addWidget(self.status_label)
        layout.addStretch(1)
        layout.addWidget(self.datetime_label)

        return status

    def _apply_styles(self):
        self.setStyleSheet(
            f"""
            QWidget {{
                font-family: "Segoe UI";
                font-size: 12px;
            }}
            #Header {{
                background: {self.colors['primary']};
                border-radius: 6px;
            }}
            #Sidebar {{
                background: {self.colors['card']};
                border: 1px solid {self.colors['border']};
                border-radius: 8px;
            }}
            QPushButton#SidebarButton {{
                background: {self.colors['white']};
                color: {self.colors['text_primary']};
                border: 1px solid {self.colors['border']};
                border-radius: 6px;
                padding: 8px 10px;
                text-align: left;
            }}
            QPushButton#SidebarButton:hover {{
                background: {self.colors['primary']};
                color: {self.colors['white']};
            }}
            QPushButton#PrimaryButton {{
                background: {self.colors['secondary']};
                color: {self.colors['white']};
                border-radius: 6px;
                padding: 6px 12px;
            }}
            QPushButton#PrimaryButton:hover {{
                background: {self.colors['primary']};
            }}
            QPushButton#SuccessButton {{
                background: {self.colors['success']};
                color: {self.colors['white']};
                border-radius: 6px;
                padding: 6px 12px;
            }}
            QPushButton#SuccessButton:hover {{
                background: #2E9B32;
            }}
            QPushButton#WarningButton {{
                background: {self.colors['warning']};
                color: {self.colors['white']};
                border-radius: 6px;
                padding: 6px 12px;
            }}
            QPushButton#WarningButton:hover {{
                background: #FF9A1F;
            }}
            QPushButton#DangerButton {{
                background: {self.colors['danger']};
                color: {self.colors['white']};
                border-radius: 6px;
                padding: 6px 12px;
            }}
            QPushButton#DangerButton:hover {{
                background: #C91E35;
            }}
            QFrame[role="card"] {{
                background: {self.colors['card']};
                border: 1px solid {self.colors['border']};
                border-radius: 8px;
            }}
            QFrame[role="card_header"] {{
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
            QFrame[role="summary_card"] {{
                background: {self.colors['card']};
                border: 1px solid {self.colors['border']};
                border-radius: 8px;
            }}
            QFrame[role="stats_block"] {{
                background: #FFFFFF;
                border: 1px solid #D8E0E8;
                border-radius: 10px;
            }}
            #StatsHeader {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                            stop: 0 {self.colors['primary']},
                                            stop: 1 {self.colors['secondary']});
                border-radius: 8px;
            }}
            #StatisticsPage {{
                background: #F5F7FA;
            }}
            QGroupBox[role="stats_group"] {{
                border: 1px solid #D8E0E8;
                border-radius: 8px;
                margin-top: 12px;
                background: #FFFFFF;
            }}
            QGroupBox[role="stats_group"]::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 6px;
                color: {self.colors['text_primary']};
                font-weight: 600;
            }}
            QGroupBox[role="sql_group"] {{
                border: 1px solid {self.colors['border']};
                border-radius: 8px;
                margin-top: 12px;
                background: #FFFFFF;
            }}
            QGroupBox[role="sql_group"]::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 6px;
                color: {self.colors['text_primary']};
                font-weight: 600;
            }}
            QGroupBox[role="settings_group"] {{
                border: 1px solid {self.colors['border']};
                border-radius: 8px;
                margin-top: 12px;
                background: #FFFFFF;
            }}
            QGroupBox[role="settings_group"]::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 6px;
                color: {self.colors['text_primary']};
                font-weight: 600;
            }}
            #SettingsPage {{
                background: #F5F7FA;
            }}
            #SqlEditor {{
                background: #2E3440;
                color: #D8DEE9;
                border: 1px solid #3B4252;
                border-radius: 6px;
                padding: 6px;
            }}
            #StatusBar {{
                background: {self.colors['card']};
                border: 1px solid {self.colors['border']};
                border-radius: 6px;
            }}
            QTableWidget {{
                background: {self.colors['white']};
                gridline-color: {self.colors['border']};
                border: 1px solid {self.colors['border']};
                selection-background-color: {self.colors['secondary']};
                selection-color: {self.colors['white']};
            }}
            QHeaderView::section {{
                background: {self.colors['primary']};
                color: {self.colors['white']};
                padding: 6px;
                border: none;
                font-weight: 600;
            }}
            """
        )

    def _start_clock(self):
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update_datetime)
        self._timer.start(1000)
        self.update_datetime()

    def update_datetime(self):
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.datetime_label.setText(now)

    def navigate(self, name):
        page = self.pages.get(name)
        if not page:
            return
        self.stack.setCurrentWidget(page)
        if name == "Dashboard":
            self.refresh_dashboard()
        elif name == "Cidadãos":
            if not self.connected:
                self.citizens_page.set_connected(False)
                QMessageBox.warning(
                    self,
                    "Aviso",
                    "Conecte-se ao banco de dados primeiro!",
                )
                return
            self.citizens_page.load_citizens()
        elif name == "Veículos":
            if not self.connected:
                self.vehicles_page.set_connected(False)
                QMessageBox.warning(
                    self,
                    "Aviso",
                    "Conecte-se ao banco de dados primeiro!",
                )
                return
            self.vehicles_page.load_vehicles()
        elif name == "Sensores":
            if not self.connected:
                self.sensors_page.set_connected(False)
                QMessageBox.warning(
                    self,
                    "Aviso",
                    "Conecte-se ao banco de dados primeiro!",
                )
                return
            self.sensors_page.load_sensors()
        elif name == "Incidentes":
            if not self.connected:
                self.incidents_page.set_connected(False)
                QMessageBox.warning(
                    self,
                    "Aviso",
                    "Conecte-se ao banco de dados primeiro!",
                )
                return
            self.incidents_page.load_incidents()
        elif name == "Multas":
            if not self.connected:
                self.fines_page.set_connected(False)
                QMessageBox.warning(
                    self,
                    "Aviso",
                    "Conecte-se ao banco de dados primeiro!",
                )
                return
            self.fines_page.load_fines()
        elif name == "Estatísticas":
            if not self.connected:
                self.statistics_page.set_connected(False)
                QMessageBox.warning(
                    self,
                    "Aviso",
                    "Conecte-se ao banco de dados primeiro!",
                )
                return
            self.statistics_page.load_statistics()
        elif name == "SQL":
            if not self.connected:
                self.sql_page.set_connected(False)
                QMessageBox.warning(
                    self,
                    "Aviso",
                    "Conecte-se ao banco de dados primeiro!",
                )
                return
            self.sql_page.load_console()
        elif name == "Configurações":
            self.settings_page.load_settings()
            self.settings_page.update_connection_state(self.connected)

    def get_connection_string(self):
        """Monta string de conexão a partir das variáveis de ambiente."""
        settings = self._load_settings_file()
        db_settings = settings.get("database", {})

        db_name = (db_settings.get("dbname") or os.getenv("DB_NAME") or "").strip()
        db_host = (db_settings.get("host") or os.getenv("DB_HOST") or "").strip()
        db_port = (db_settings.get("port") or os.getenv("DB_PORT") or "").strip()
        db_user = (os.getenv("DB_USER") or "").strip()
        db_password = (os.getenv("DB_PASSWORD") or "").strip()

        if not all([db_name, db_user, db_password, db_host]):
            raise Exception("Variáveis de ambiente do banco não configuradas")

        parts = [
            f"dbname={db_name}",
            f"user={db_user}",
            f"password={db_password}",
            f"host={db_host}",
        ]
        if db_port:
            parts.append(f"port={db_port}")
        return " ".join(parts)

    def _load_settings_file(self):
        settings_path = os.path.join(ROOT_DIR, "settings.json")
        if not os.path.exists(settings_path):
            return {}
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def is_username_available(self, username):
        try:
            conn_string = self.get_connection_string()
            with psy.connect(conn_string) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id FROM app_user_active WHERE username = %s",
                        (username,),
                    )
                    return cur.fetchone() is None
        except Exception:
            return False

    def toggle_connection(self):
        if self.connected:
            self.connected = False
            self.connection_status.setText("🔴 Desconectado")
            self.connect_button.setText("🔌 Conectar")
            self.status_label.setText("Desconectado do banco")
            self.dashboard_page.set_connected(False)
            self.citizens_page.set_connected(False)
            self.vehicles_page.set_connected(False)
            self.sensors_page.set_connected(False)
            self.incidents_page.set_connected(False)
            self.fines_page.set_connected(False)
            self.statistics_page.set_connected(False)
            self.sql_page.set_connected(False)
            self.settings_page.update_connection_state(False)
            return

        try:
            conn_string = self.get_connection_string()
            with psy.connect(conn_string) as conn:
                pass
            self.connected = True
            self.connection_status.setText("🟢 Conectado")
            self.connect_button.setText("🔌 Desconectar")
            self.status_label.setText("Conectado ao banco")
            self.dashboard_page.set_connected(True)
            self.citizens_page.set_connected(True)
            self.vehicles_page.set_connected(True)
            self.sensors_page.set_connected(True)
            self.incidents_page.set_connected(True)
            self.fines_page.set_connected(True)
            self.statistics_page.set_connected(True)
            self.sql_page.set_connected(True)
            self.settings_page.update_connection_state(True)
            self.refresh_dashboard()
            if self.stack.currentWidget() is self.citizens_page:
                self.citizens_page.load_citizens()
            if self.stack.currentWidget() is self.vehicles_page:
                self.vehicles_page.load_vehicles()
            if self.stack.currentWidget() is self.sensors_page:
                self.sensors_page.load_sensors()
            if self.stack.currentWidget() is self.incidents_page:
                self.incidents_page.load_incidents()
            if self.stack.currentWidget() is self.fines_page:
                self.fines_page.load_fines()
            if self.stack.currentWidget() is self.statistics_page:
                self.statistics_page.load_statistics()
            if self.stack.currentWidget() is self.sql_page:
                self.sql_page.load_console()
            if self.stack.currentWidget() is self.settings_page:
                self.settings_page.load_settings()
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Erro de conexão",
                f"Não foi possível conectar ao banco de dados.\n{exc}",
            )

    def refresh_dashboard(self):
        if not self.connected:
            self.dashboard_page.set_connected(False)
            return

        try:
            conn_string = self.get_connection_string()
            with psy.connect(conn_string) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    stats = {}

                    cur.execute(
                          """
                          SELECT COUNT(*) as total,
                                 COUNT(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as this_month
                          FROM app_user_active
                          """
                    )
                    stats["users"] = cur.fetchone()

                    cur.execute(
                        """
                        SELECT COUNT(*) as total,
                               COUNT(CASE WHEN debt > 0 THEN 1 END) as with_debt,
                               COALESCE(SUM(debt), 0) as total_debt
                        FROM citizen_active
                        """
                    )
                    stats["citizens"] = cur.fetchone()

                    cur.execute(
                        """
                        SELECT COUNT(*) as total,
                               COUNT(CASE WHEN allowed = TRUE THEN 1 END) as active
                        FROM vehicle_active
                        """
                    )
                    stats["vehicles"] = cur.fetchone()

                    cur.execute(
                        """
                        SELECT COUNT(*) as total,
                               COUNT(CASE WHEN occurred_at >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as this_week
                        FROM traffic_incident
                        """
                    )
                    stats["incidents"] = cur.fetchone()

                    cur.execute(
                        """
                        SELECT COUNT(*) as total,
                               COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                               COUNT(CASE WHEN status = 'overdue' THEN 1 END) as overdue,
                               COALESCE(SUM(amount), 0) as total_amount
                        FROM fine
                        """
                    )
                    stats["fines"] = cur.fetchone()

                    cur.execute(
                        """
                        SELECT COUNT(*) as total,
                               COUNT(CASE WHEN active = TRUE THEN 1 END) as active
                        FROM sensor_active
                        """
                    )
                    stats["sensors"] = cur.fetchone()

            cards_data = [
                (
                    "👤 Usuários",
                    stats["users"]["total"],
                    f"Novos este mês: {stats['users']['this_month']}",
                    "Usuários ativos no sistema",
                    self.colors["primary"],
                ),
                (
                    "👥 Cidadãos",
                    stats["citizens"]["total"],
                    f"Com dívida: {stats['citizens']['with_debt']}",
                    format_currency_brl(stats["citizens"]["total_debt"]),
                    self.colors["success"],
                ),
                (
                    "🚗 Veículos",
                    stats["vehicles"]["total"],
                    f"Ativos: {stats['vehicles']['active']}",
                    f"{stats['vehicles']['total'] - stats['vehicles']['active']} bloqueados",
                    self.colors["warning"],
                ),
                (
                    "⚠️ Incidentes",
                    stats["incidents"]["total"],
                    f"Esta semana: {stats['incidents']['this_week']}",
                    f"Média: {stats['incidents']['total'] / 30:.1f}/dia",
                    self.colors["accent"],
                ),
                (
                    "💰 Multas",
                    stats["fines"]["total"],
                    f"Pendentes: {stats['fines']['pending']}",
                    format_currency_brl(stats["fines"]["total_amount"]),
                    self.colors["secondary"],
                ),
                (
                    "📹 Sensores",
                    stats["sensors"]["total"],
                    f"Ativos: {stats['sensors']['active']}",
                    f"{stats['sensors']['total'] - stats['sensors']['active']} inativos",
                    self.colors["dark"],
                ),
            ]

            self.dashboard_page.set_connected(True)
            self.dashboard_page.update_cards(cards_data)
            self.status_label.setText("Dashboard atualizado")
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Erro ao carregar dashboard",
                f"Erro ao carregar estatísticas.\n{exc}",
            )


def run():
    app = QApplication(sys.argv)
    app_font = app.font()
    if app_font.pointSize() <= 0:
        app_font.setPointSize(10)
        app.setFont(app_font)
    window = SmartCityOSQtApp()

    icon_path = os.path.join(ROOT_DIR, "gui", "icon.ico")
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))

    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
