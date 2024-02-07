from django.shortcuts import render


def view_logs(request):
    # Чтение содержимого файла логов
    with open('telegram_bot.log', 'r') as log_file:
        log_lines = log_file.readlines()
    # Передача содержимого файла логов в шаблон
    return render(request, 'logs.html', {'log_lines': log_lines})
