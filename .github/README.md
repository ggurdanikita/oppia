# [Oppia](https://www.oppia.org) [![CircleCI](https://circleci.com/gh/oppia/oppia/tree/develop.svg?style=svg)](https://circleci.com/gh/oppia/oppia/tree/develop) [![Build Status](https://travis-ci.com/oppia/oppia.svg?branch=develop)](https://travis-ci.com/github/oppia/oppia) [![codecov](https://codecov.io/gh/oppia/oppia/branch/develop/graph/badge.svg)](https://codecov.io/gh/oppia/oppia) [![Join the chat at https://gitter.im/oppia/oppia-chat](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/oppia/oppia-chat?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Oppia is an online learning tool that enables anyone to easily create and share interactive activities (called 'explorations'). These activities simulate a one-on-one conversation with a tutor, making it possible for students to learn by doing while getting feedback.

In addition to developing the Oppia platform, the team is also developing and piloting a set of free and effective [lessons](https://www.oppia.org/fractions) on basic mathematics. These lessons are targeted at learners who lack access to educational resources.

Oppia is written using Python and AngularJS, and is built on top of Google App Engine.

  * [Oppia.org community site](https://www.oppia.org)
  * [User Documentation](https://oppia.github.io/)
  * [Contributors' wiki](https://github.com/oppia/oppia/wiki)
  * [Developer mailing list](http://groups.google.com/group/oppia-dev)
  * [File an issue](https://github.com/oppia/oppia/issues/new/choose)

<p align="center">
  <a href="http://www.youtube.com/watch?v=Ntcw0H0hwPU" target="_blank" rel="noopener">
    <img src="https://cloud.githubusercontent.com/assets/8845039/16814722/b219cac0-4954-11e6-9573-c37557d1b410.png">
  </a>
</p>

## Installation

Please refer to the [Installing Oppia page](https://github.com/oppia/oppia/wiki/Installing-Oppia) for full instructions.

## Contributing

The Oppia project is built by the community for the community. We welcome contributions from everyone, especially new contributors.

You can help with Oppia's development in many ways, including art, coding, design and documentation.
  * **Developers**: please see [this wiki page](https://github.com/oppia/oppia/wiki/Contributing-code-to-Oppia#setting-things-up) for instructions on how to set things up and commit changes.
  * **All other contributors**: please see our [general contributor guidelines](https://github.com/oppia/oppia/wiki).


## Support

If you have any feature requests or bug reports, please log them on our [issue tracker](https://github.com/oppia/oppia/issues/new/choose).

Please report security issues directly to admin@oppia.org.


## License

The Oppia code is released under the [Apache v2 license](https://github.com/oppia/oppia/blob/develop/LICENSE).


## Keeping in touch

  * [Blog](https://medium.com/oppia-org)
  * [Discussion forum](http://groups.google.com/group/oppia)
  * [Announcements mailing list](http://groups.google.com/group/oppia-announce)
  * Social media: [YouTube](https://www.youtube.com/channel/UC5c1G7BNDCfv1rczcBp9FPw), [FB](https://www.facebook.com/oppiaorg), [Twitter](https://twitter.com/oppiaorg)

We also have public chat rooms on Gitter: [https://gitter.im/oppia/oppia-chat](https://gitter.im/oppia/oppia-chat). Drop by and say hello!


## Oppia forked version

### Бранч

Перед запуском платформы нужно переключиться на ветку `new_auth`

### Что изменилось?

Платформа была разработана для использования в среде **Google App Engine**(GAE). Вход в платформу осуществлялся с 
использование google-аккаунта. Т.е. при входе в платформу, нужно было ввести логин/пароль от google-аккаунта.

Есть возможность запуска платформы с локальным сервером GAE.
Запуск платформы с локальным сервером GAE был расчитан на разработчиков, а не для продакшена. Поэтому, авторизация
выглядит еще проще. Достаточно ввести любой валидный email. Это было сделано для простоты создания пользователей с разными почтовыми ящиками.

Сейчас же планируется использовать платформу с локальным сервером GAE в продакшене. Поэтому, необходимо было переделать
систему регистрации/авторизации. В этом и есть отличие текущей fork-версии от оригинала.

### Хэндлеры

#### GET /_ah/login_proxy

В вервыу очередь, нужно было запретить авторизацию только по email. Для этого использовался хэндлер **/_ah/login** c параметром **action=Login**.
На BE реализован хэнделер **/_ah/login_proxy** - делает все тоже самое что и **/_ah/login**, но не позволяет авторизоваться только по email.
Нужно изменить все вызовы **/_ah/login** на вызовы **/_ah/login_proxy**

#### POST /custom_auth

Используется для авторизации по почте и паролю.
В параметрах пути нужно передать: `?email=test@example.com&action=Login&continue=http://mydomain.com/signup?return_url=/`, где:
- email - email пользователя
- mydomain.com - домен- ресурса

payload={"password":"Ru77Kq67", "email":"test@example.com"}

#### POST /password_recovery_token

Отправляет письмо с токеном на восстановление пароля 
Принимает:
payload={"email":"test@example.com"}
Пользователю будет отправлено письмо со ссылкой типа: http://localhost:8181/password_recovery?token=51099f9044f94351a516a94e1a852e2f
Перейдя по ссылке он должен ввести новый пароль и нажать кнопку "применить". По нажатию на кнопку, нужно отправить
POST-запрос `/token/<token>/password_recovery`. <token> - это токен с которым пришел пользователь. payload={"password":"NEW_PASS"}

#### POST /email_confirm_token

Отправляет письмо с токеном на подтверждения почты
Принимает:
payload={"email":"test@example.com"}
Пользователю будет отправлено письмо со ссылкой типа: http://localhost:8181/email_confirm?token=ff4848a0e4d54cd19582094b002307b8
Перейдя по ссылке, пользователь должен попасть на страцицу откуда выполнится POST-запрос `/token/<token>/email_confirm`. <token> - это токен с которым пришел пользователь.
payload={}

#### POST /signuphandler/data

Доработан. Используется для создания новых пользователей.
Кроме username теперь еще принимает email, пароль(password) и роль(role). Роль может иметь одно из 2-х значений:
- EXPLORATION_EDITOR - учитель
- LEARNER - ученик

Все параметры обязательны.

#### Общее для хэндлеров

Везде, где после выполнения запроса происходит редирект, нужно поправить адрес редиректа. Сейчас даже если приложение открыто на 80-ом порту, после регистрации(или других действий) перебрасывает на порт 8181. Нужно поправить, чтоб редирект
происходил на 80-й. На сколько я понял, это зависит от параметра `continue` в параметрах запроса.

### Nginx

Nginx необходим для запрета старой системы авторизации(только по email)
Платформа поднимается на порту 8181, а nginx на 80. Наружу светим 80. Перенаправляем все запросы c 80 на 8181 кроме
запросов на `/_ah/login`, таким образом запретим старую авторизацию.

#### Установка nginx

```bash
sudo apt update
sudo apt install nginx
sudo systemctl enable nginx
```

#### Настройка nginx

1. Переходим в дирректорию с oppia
2. Перезаписываем файл и перезапускаем nginx
```bash
sudo systemctl stop nginx
sudo cat nginx.conf > /etc/nginx/nginx.conf
sudo systemctl start nginx
```
