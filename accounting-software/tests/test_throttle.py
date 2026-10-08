from auth_throttle import AttemptLimiter


def test_email_limit_is_independent_of_transport_ip_and_case():
    now = [0]
    limiter = AttemptLimiter(clock=lambda: now[0])
    limits = {'ip': 100, 'email': 2, 'window': 300}
    assert limiter.consume('login','ip-a','USER@fixture.invalid',limits) == 0
    assert limiter.consume('login','ip-b','user@fixture.invalid',limits) == 0
    assert limiter.consume('login','ip-c','user@fixture.invalid',limits) > 0
    now[0] = 301
    assert limiter.consume('login','ip-c','user@fixture.invalid',limits) == 0


def test_ip_limit_is_independent_of_email_and_capacity_is_bounded():
    limiter = AttemptLimiter(capacity=6)
    limits = {'ip': 2, 'email': 100, 'window': 300}
    assert limiter.consume('register','same-ip','a@fixture.invalid',limits) == 0
    assert limiter.consume('register','same-ip','b@fixture.invalid',limits) == 0
    assert limiter.consume('register','same-ip','c@fixture.invalid',limits) > 0
    for i in range(20): limiter.consume('register',str(i),str(i),limits)
    assert len(limiter.buckets) <= 6
