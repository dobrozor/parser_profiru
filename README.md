# Парсер Profi.ru

### ПАРСЕР РАБОТАЕТ, но я работаю над тем, чтоб убрать selenium из использования и завязать всё на реквестах, если хочешь помочь мне, можешь читать всё что я нарыл и писать свои обдумывания сюда https://t.me/pro_parser_profi

Парсер для заказов фриланса с сервиса profi.ru. Всё работает на selenium и bs4. Простой анализ сайта, проверяет классы.
Из плюсов:
1) не нагружает сам сервис аптаймом, а значит нет рисков получить бан сервиса
2) есть поиск по ключевым словам заказа. Тоесть если в ваш фильтр поиска профи.ру попадает сомнительный заказ (например ОПРОСЫ ЗА 900 РУБЛЕЙ) и прочее, он их фильтрует
3) Бот автоматически понимает какие заказы уже вам отправил и не будет спамить одним и тем же заказом
4) есть примитивная фильтрация по времени. Если заказ создан более 1 часа назад он не будет отправляться в тг

Пока что это всё. Автоматического отклика здесь нет, так как это может нарушать правила сервиса. Надеюсь в скором времени напишу чтоб бот так же уведомлял о новых сообщениях в чатах

А теперь главный вопрос, зачем это? У сервиса есть приложение на андройд и иос, но проблема обоих, что они НЕ ВСЕГДА выводят уведомления. Именно потому, чтоб быстро откликнуться на хороший заказ, нужно сидеть и мониторить вечно обновляя страницу профи.ру, вот я и подумал что будет проще, если эту муторную работу сделает бот, а мы получим уже отфильтрованные новые заказы, который 100% придут и уведомления телеграм нам пришел, к тому же можно выключить уведомления канала и не получать уведомления (если вы в отдыхе).

## ОБНОВЛЕНИЕ 2.0
Я изменил подход авторизации. Теперь вам нужно будет один раз запустить файл get_cookies пройти авторизацию на сервисе, файл автоматически сохранит куки файлы вашего аккаунта. И уже потом файл session будет использоваться bot.py для парсинга. Таким образом не нужно хранить логин и пароль в файле TXT


Таким образом получился простой и понятный парсер, надеюсь на ваши лайки. Если чтоЮ обратная связь в том же телеграме t.me/dobrozor
