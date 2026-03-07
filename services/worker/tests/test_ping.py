from worker_app.tasks.ping import ping


def test_ping():
    result = ping()
    assert result == "pong"
