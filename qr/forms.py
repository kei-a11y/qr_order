from django import forms
from .models import StoreSettings, Table, MenuCategory, MenuItem, Order

class LoginForm(forms.Form):
    """ログインフォーム"""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'パスワードを入力してください'
        }),
        label='パスワード'
    )

class StoreSettingsForm(forms.ModelForm):
    """店舗設定フォーム"""
    class Meta:
        model = StoreSettings
        fields = ['password', 'wifi_ssid', 'wifi_password', 'wifi_security', 'server_ip']
        widgets = {
            'password': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'ログイン用パスワードを設定してください'
            }),
            'wifi_ssid': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例: StoreWiFi'
            }),
            'wifi_password': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'WiFiのパスワード'
            }),
            'wifi_security': forms.Select(attrs={
                'class': 'form-select'
            }),
            'server_ip': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例: 192.168.1.100'
            }),
        }
        labels = {
            'password': 'ログイン用パスワード',
            'wifi_ssid': 'WiFiのSSID',
            'wifi_password': 'WiFiのパスワード',
            'wifi_security': 'セキュリティタイプ',
            'server_ip': 'サーバーのIPアドレス',
        }

class TableForm(forms.ModelForm):
    """テーブル設定フォーム"""
    class Meta:
        model = Table
        fields = ['table_number', 'is_active']
        widgets = {
            'table_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'table_number': 'テーブル番号',
            'is_active': '有効',
        }

class TableCountForm(forms.Form):
    """テーブル数設定フォーム"""
    table_count = forms.IntegerField(
        min_value=1,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '設定したいテーブル数を入力'
        }),
        label='テーブル数'
    )

class MenuCategoryForm(forms.ModelForm):
    """メニューカテゴリフォーム"""
    class Meta:
        model = MenuCategory
        fields = ['name', 'order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'カテゴリ名を入力'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'カテゴリ名',
            'order': '表示順',
            'is_active': '有効',
        }

class MenuItemForm(forms.ModelForm):
    """メニュー項目フォーム"""
    class Meta:
        model = MenuItem
        fields = ['category', 'name', 'description', 'price', 'image', 'is_available', 'order']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'メニュー名を入力'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'メニューの説明を入力'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'is_available': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'category': 'カテゴリ',
            'name': 'メニュー名',
            'description': '説明',
            'price': '価格（円）',
            'image': '画像',
            'is_available': '提供可能',
            'order': '表示順',
        }

class OrderStatusForm(forms.ModelForm):
    """注文ステータス更新フォーム"""
    class Meta:
        model = Order
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
        }