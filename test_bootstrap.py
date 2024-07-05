import pytest


@pytest.mark.usefixtures('generate_test_render')
class TestStarter(object):

    def test_start(self):
        pytest.skip('此为测试启动方法, 不执行')
