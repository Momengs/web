from models.user import User


def test():
    form = dict(
        username='guagua',
        password='123',
    )
    u = User.new(form)
    u.save()


if __name__ == '__main__':
    test()
