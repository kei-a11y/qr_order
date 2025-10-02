import json
import qrcode
import io
import base64
import time
from PIL import Image, ImageDraw, ImageFont
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Sum, Count
from django.conf import settings
from pathlib import Path
from .models import StoreSettings, Table, MenuCategory, MenuItem, Order, OrderItem
from .forms import LoginForm, StoreSettingsForm, TableForm, TableCountForm, MenuCategoryForm, MenuItemForm, OrderStatusForm

# config.jsonのパス
CONFIG_PATH = Path(settings.BASE_DIR) / "config.json"

def get_client_ip(request):
    """クライアントのIPアドレスを取得"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def check_wifi_connection(request):
    """WiFi接続チェック"""
    try:
        store_settings = StoreSettings.objects.first()
        if not store_settings:
            return False
        
        client_ip = get_client_ip(request)
        server_ip = store_settings.server_ip
        
        # 同じネットワーク内かチェック（簡易版）
        # 実際の実装では、より詳細なネットワークチェックが必要
        client_network = '.'.join(client_ip.split('.')[:-1])
        server_network = '.'.join(server_ip.split('.')[:-1])
        
        return client_network == server_network
    except:
        return False

def index(request):
    """トップページ（ログイン画面）"""
    # 初期設定が済んでいるかチェック
    if not StoreSettings.objects.exists():
        return redirect('initial_setup')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            store_settings = StoreSettings.objects.first()
            
            if store_settings and store_settings.password == password:
                request.session['authenticated'] = True
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'パスワードが正しくありません。')
    else:
        form = LoginForm()
    
    return render(request, 'qr/login.html', {'form': form})

def initial_setup(request):
    """初期設定画面"""
    if StoreSettings.objects.exists():
        return redirect('index')
    
    if request.method == 'POST':
        form = StoreSettingsForm(request.POST)
        if form.is_valid():
            store_settings = form.save()
            
            # config.jsonにサーバーIPを保存
            server_ip = form.cleaned_data['server_ip']
            try:
                with open(CONFIG_PATH, "w") as f:
                    json.dump({"USER_IP": server_ip}, f)
                
                messages.success(request, '初期設定が完了しました。サーバーを再起動します...')
                
                # settings.pyのタイムスタンプを更新して自動再起動を促す
                settings_file = Path(settings.BASE_DIR) / "kk1" / "settings.py"
                if settings_file.exists():
                    settings_file.touch()
                
                # 再起動待ち画面を表示
                context = {
                    'server_ip': server_ip,
                    'new_url': f'http://{server_ip}:8000'
                }
                return render(request, 'qr/restart_wait.html', context)
                
            except Exception as e:
                messages.error(request, f'設定の保存中にエラーが発生しました: {e}')
                store_settings.delete()  # エラー時は設定を削除
    else:
        form = StoreSettingsForm()
    
    return render(request, 'qr/initial_setup.html', {'form': form})

def admin_required(view_func):
    """管理者認証デコレータ"""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('authenticated'):
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return wrapper

@admin_required
def admin_dashboard(request):
    """管理者ダッシュボード"""
    total_tables = Table.objects.count()
    total_menu_items = MenuItem.objects.count()
    # 提供未了の注文件数（delivered と cancelled 以外）
    today_orders = Order.objects.exclude(status__in=['delivered', 'cancelled']).count()
    
    context = {
        'total_tables': total_tables,
        'total_menu_items': total_menu_items,
        'today_orders': today_orders,
    }
    return render(request, 'qr/admin_dashboard.html', context)

@admin_required
def settings(request):
    """システム設定"""
    store_settings = StoreSettings.objects.first()
    
    if request.method == 'POST':
        old_ip = store_settings.server_ip if store_settings else None
        form = StoreSettingsForm(request.POST, instance=store_settings)
        if form.is_valid():
            store_settings = form.save()
            new_ip = store_settings.server_ip
            
            # IPアドレスが変更された場合、config.jsonを更新
            if old_ip != new_ip:
                try:
                    with open(CONFIG_PATH, "w") as f:
                        json.dump({"USER_IP": new_ip}, f)
                    
                    # settings.pyのタイムスタンプを更新
                    settings_file = Path(settings.BASE_DIR) / "kk1" / "settings.py"
                    if settings_file.exists():
                        settings_file.touch()
                    
                    messages.success(request, 'システム設定を更新しました。サーバーIPが変更されたため、サーバーを再起動してください。')
                    
                    # IPアドレス変更時の再起動待ち画面
                    context = {
                        'server_ip': new_ip,
                        'new_url': f'http://{new_ip}:8000',
                        'is_ip_change': True
                    }
                    return render(request, 'qr/restart_wait.html', context)
                    
                except Exception as e:
                    messages.error(request, f'config.jsonの更新中にエラーが発生しました: {e}')
            else:
                messages.success(request, 'システム設定を更新しました。')
            
            return redirect('settings')
    else:
        form = StoreSettingsForm(instance=store_settings)
    
    context = {
        'form': form,
        'store_settings': store_settings
    }
    return render(request, 'qr/settings.html', context)

@admin_required
def menu_management(request):
    """メニュー管理"""
    categories = MenuCategory.objects.prefetch_related('items').all()
    return render(request, 'qr/menu_management.html', {'categories': categories})

@admin_required
def add_category(request):
    """カテゴリ追加"""
    if request.method == 'POST':
        form = MenuCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'カテゴリを追加しました。')
            return redirect('menu_management')
    else:
        form = MenuCategoryForm()
    
    return render(request, 'qr/add_category.html', {'form': form})

@admin_required
def edit_category(request, category_id):
    """カテゴリ編集"""
    category = get_object_or_404(MenuCategory, id=category_id)
    
    if request.method == 'POST':
        form = MenuCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'カテゴリを更新しました。')
            return redirect('menu_management')
    else:
        form = MenuCategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'is_edit': True
    }
    return render(request, 'qr/add_category.html', context)

@admin_required
def delete_category(request, category_id):
    """カテゴリ削除"""
    category = get_object_or_404(MenuCategory, id=category_id)
    
    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'カテゴリ「{category_name}」を削除しました。')
        return redirect('menu_management')
    
    context = {
        'category': category,
        'menu_items_count': category.items.count()
    }
    return render(request, 'qr/delete_category.html', context)

@admin_required
def add_menu_item(request):
    """メニュー項目追加"""
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'メニューを追加しました。')
            return redirect('menu_management')
    else:
        form = MenuItemForm()
    
    return render(request, 'qr/add_menu_item.html', {'form': form})

@admin_required
def edit_menu_item(request, item_id):
    """メニュー項目編集"""
    menu_item = get_object_or_404(MenuItem, id=item_id)
    
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES, instance=menu_item)
        if form.is_valid():
            form.save()
            messages.success(request, 'メニューを更新しました。')
            return redirect('menu_management')
    else:
        form = MenuItemForm(instance=menu_item)
    
    context = {
        'form': form,
        'menu_item': menu_item,
        'is_edit': True
    }
    return render(request, 'qr/add_menu_item.html', context)

@admin_required
def delete_menu_item(request, item_id):
    """メニュー項目削除"""
    menu_item = get_object_or_404(MenuItem, id=item_id)
    
    if request.method == 'POST':
        item_name = menu_item.name
        menu_item.delete()
        messages.success(request, f'メニュー「{item_name}」を削除しました。')
        return redirect('menu_management')
    
    context = {
        'menu_item': menu_item
    }
    return render(request, 'qr/delete_menu_item.html', context)

@admin_required
def table_management(request):
    """テーブル管理"""
    tables = Table.objects.all()
    
    if request.method == 'POST':
        form = TableCountForm(request.POST)
        if form.is_valid():
            table_count = form.cleaned_data['table_count']
            
            # 既存のテーブル数を取得
            existing_count = Table.objects.count()
            
            if table_count > existing_count:
                # テーブルを追加
                for i in range(existing_count + 1, table_count + 1):
                    Table.objects.create(table_number=i)
                messages.success(request, f'テーブルを{table_count}個に設定しました。')
            else:
                messages.info(request, f'現在のテーブル数は{existing_count}個です。')
            
            return redirect('table_management')
    else:
        form = TableCountForm()
    
    context = {
        'tables': tables,
        'form': form,
    }
    return render(request, 'qr/table_management.html', context)

@admin_required
def generate_qr_codes(request, table_id):
    """QRコード生成"""
    table = get_object_or_404(Table, id=table_id)
    store_settings = StoreSettings.objects.first()
    
    if not store_settings:
        messages.error(request, '店舗設定が完了していません。')
        return redirect('table_management')
    
    # WiFi接続用QRコード（WIFI形式）
    wifi_data = f"WIFI:T:{store_settings.wifi_security};S:{store_settings.wifi_ssid};P:{store_settings.wifi_password};;"
    
    # 注文用QRコード
    order_url = f"http://{store_settings.server_ip}:8000/order/{table.table_number}/"
    
    # QRコード画像生成
    wifi_qr = qrcode.QRCode(version=1, box_size=8, border=3)
    wifi_qr.add_data(wifi_data)
    wifi_qr.make(fit=True)
    wifi_img = wifi_qr.make_image(fill_color="black", back_color="white")
    
    order_qr = qrcode.QRCode(version=1, box_size=8, border=3)
    order_qr.add_data(order_url)
    order_qr.make(fit=True)
    order_img = order_qr.make_image(fill_color="black", back_color="white")
    
    # キャンバスサイズ（A4サイズに近い比率）
    img_width = 1000
    img_height = 1400
    
    # 背景色（明るいグレー）
    combined_img = Image.new('RGB', (img_width, img_height), '#f8f9fa')
    draw = ImageDraw.Draw(combined_img)
    
    # タイトル背景（上部バー）
    draw.rectangle([(0, 0), (img_width, 100)], fill='#4a90e2')
    
    # フォント設定
    try:
        # 日本語フォントの読み込みを試みる（環境に応じて調整が必要）
        title_font = ImageFont.truetype("C:/Windows/Fonts/msgothic.ttc", 40)
        large_font = ImageFont.truetype("C:/Windows/Fonts/msgothic.ttc", 32)
        medium_font = ImageFont.truetype("C:/Windows/Fonts/msgothic.ttc", 28)
        small_font = ImageFont.truetype("C:/Windows/Fonts/msgothic.ttc", 24)
    except:
        # フォントが見つからない場合はデフォルト
        title_font = ImageFont.load_default()
        large_font = ImageFont.load_default()
        medium_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # タイトル（テーブル番号）
    title_text = f"テーブル {table.table_number}"
    # テキストサイズを取得（PIL 10.0.0以降）
    try:
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
    except:
        title_width = len(title_text) * 20
    
    draw.text(((img_width - title_width) // 2, 30), title_text, fill='white', font=title_font)
    
    # メインメッセージ
    y_pos = 130
    message1 = "当店では、QRコードによる注文も可能です。"
    message2 = "下記の手順でスマホから注文できます。"
    
    try:
        msg1_bbox = draw.textbbox((0, 0), message1, font=medium_font)
        msg1_width = msg1_bbox[2] - msg1_bbox[0]
        msg2_bbox = draw.textbbox((0, 0), message2, font=medium_font)
        msg2_width = msg2_bbox[2] - msg2_bbox[0]
    except:
        msg1_width = len(message1) * 12
        msg2_width = len(message2) * 12
    
    draw.text(((img_width - msg1_width) // 2, y_pos), message1, fill='#333333', font=medium_font)
    draw.text(((img_width - msg2_width) // 2, y_pos + 40), message2, fill='#333333', font=medium_font)
    
    # STEP 1 セクション
    y_pos = 230
    # 背景ボックス
    draw.rectangle([(80, y_pos), (img_width - 80, y_pos + 500)], fill='white', outline='#4a90e2', width=3)
    
    # STEP 1 ラベル
    draw.ellipse([(120, y_pos + 20), (200, y_pos + 100)], fill='#ff6b6b')
    step1_text = "STEP"
    step1_num = "1"
    try:
        step_bbox = draw.textbbox((0, 0), step1_text, font=small_font)
        step_width = step_bbox[2] - step_bbox[0]
        num_bbox = draw.textbbox((0, 0), step1_num, font=large_font)
        num_width = num_bbox[2] - num_bbox[0]
    except:
        step_width = 40
        num_width = 20
    
    draw.text(((160 - step_width // 2), y_pos + 35), step1_text, fill='white', font=small_font)
    draw.text(((160 - num_width // 2), y_pos + 55), step1_num, fill='white', font=large_font)
    
    # STEP 1 説明
    step1_desc = "まずは、下のQRコードを読み込んで店のWiFiに"
    step1_desc2 = "接続してください"
    draw.text((230, y_pos + 40), step1_desc, fill='#333333', font=medium_font)
    draw.text((230, y_pos + 70), step1_desc2, fill='#333333', font=medium_font)
    
    # WiFi QRコード配置
    wifi_img = wifi_img.resize((375, 375))
    combined_img.paste(wifi_img, ((img_width - 375) // 2, y_pos + 110))
    
    # SSID表示 いらない
    #ssid_text = f"WiFi名: {store_settings.wifi_ssid}"
    #try:
    #    ssid_bbox = draw.textbbox((0, 0), ssid_text, font=small_font)
    #    ssid_width = ssid_bbox[2] - ssid_bbox[0]
    #except:
    #    ssid_width = len(ssid_text) * 10
    #
    #draw.text(((img_width - ssid_width) // 2, y_pos + 390), ssid_text, fill='#666666', font=small_font)
    
    # STEP 2 セクション
    y_pos = 750
    # 背景ボックス
    draw.rectangle([(80, y_pos), (img_width - 80, y_pos + 500)], fill='white', outline='#4a90e2', width=3)
    
    # STEP 2 ラベル
    draw.ellipse([(120, y_pos + 20), (200, y_pos + 100)], fill='#51cf66')
    step2_num = "2"
    try:
        num2_bbox = draw.textbbox((0, 0), step2_num, font=large_font)
        num2_width = num2_bbox[2] - num2_bbox[0]
    except:
        num2_width = 20
    
    draw.text(((160 - step_width // 2), y_pos + 35), step1_text, fill='white', font=small_font)
    draw.text(((160 - num2_width // 2), y_pos + 55), step2_num, fill='white', font=large_font)
    
    # STEP 2 説明
    step2_desc = "次に注文用の下のQRコードを読み取って"
    step2_desc2 = "注文してください"
    draw.text((230, y_pos + 40), step2_desc, fill='#333333', font=medium_font)
    draw.text((230, y_pos + 70), step2_desc2, fill='#333333', font=medium_font)
    
    # 注文用QRコード配置
    order_img = order_img.resize((375, 375))
    combined_img.paste(order_img, ((img_width - 375) // 2, y_pos + 110))
    
    # 注意事項セクション
    y_pos = 1280

    draw.rectangle([(80, y_pos), (img_width - 80, y_pos + 80)], fill='#fff9e6', outline='#ffd43b', width=2)
    
    notice_icon = "※"
    notice_text = "※送信した注文をキャンセルしたい場合は店員にお申し付けください。"
    notice_text2 = ""
    
    #draw.text((120, y_pos + 20), notice_icon, fill='#ff6b6b', font=large_font)
    draw.text((110, y_pos + 30), notice_text, fill='#666666', font=small_font)
    #draw.text((160, y_pos + 60), notice_text2, fill='#666666', font=small_font)
    
    # フッター　いらない
    #footer_text = "ご不明な点がございましたら、お気軽にスタッフまでお声がけください。"
    #try:
    #    footer_bbox = draw.textbbox((0, 0), footer_text, font=small_font)
    #    footer_width = footer_bbox[2] - footer_bbox[0]
    #except:
    #    footer_width = len(footer_text) * 10
    #
    #draw.text(((img_width - footer_width) // 2, 1320), footer_text, fill='#999999', font=small_font)
    
    # 画像をレスポンスとして返す
    response = HttpResponse(content_type="image/png")
    combined_img.save(response, "PNG")
    
    response['Content-Disposition'] = f'attachment; filename="table_{table.table_number}_qr.png"'
    
    return response

def order_menu(request, table_number):
    """注文画面"""
    # WiFi接続チェック
    #if not check_wifi_connection(request):
    #    return render(request, 'qr/wifi_error.html')
    
    table = get_object_or_404(Table, table_number=table_number, is_active=True)
    categories = MenuCategory.objects.filter(is_active=True).prefetch_related('items').all()
    
    context = {
        'table': table,
        'categories': categories,
    }
    return render(request, 'qr/order_menu.html', context)

@csrf_exempt
def submit_order(request):
    """注文送信"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            table_number = data.get('table_number')
            items = data.get('items', [])
            notes = data.get('notes', '')
            
            table = get_object_or_404(Table, table_number=table_number, is_active=True)
            
            # 注文作成
            order = Order.objects.create(
                table=table,
                notes=notes
            )
            
            total_amount = 0
            for item_data in items:
                menu_item = get_object_or_404(MenuItem, id=item_data['id'])
                quantity = int(item_data['quantity'])
                
                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=quantity,
                    unit_price=menu_item.price,
                    notes=item_data.get('notes', '')
                )
                
                total_amount += menu_item.price * quantity
            
            order.total_amount = total_amount
            order.save()
            
            return JsonResponse({'status': 'success', 'order_id': order.id})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@admin_required
def kitchen_view(request):
    """厨房画面"""
    orders = Order.objects.select_related('table').prefetch_related('items__menu_item').order_by('created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'qr/kitchen_view.html', context)

@admin_required
def update_order_status(request, order_id):
    """注文ステータス更新"""
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'})

def logout(request):
    """ログアウト"""
    request.session.flush()
    return redirect('index')