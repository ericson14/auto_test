import allure
import builtins
import os
import re
import types
import pytest

from start import main


def gen_function(express, namespace={}):
    """
    动态生成函数对象, 函数作用域默认设置为builtins.__dict__，并合并namespace的变量
    :param express: 函数表达式，示例 'def foobar(): return "foobar"'
    :param namespace
    :return:
    """
    builtins.__dict__.update(namespace)
    module_code = compile(express, '', 'exec')
    function_code = [c for c in module_code.co_consts if isinstance(c, types.CodeType)][0]
    return types.FunctionType(function_code, builtins.__dict__)


def validator(response, validata):
    result = response.get("response").get("data")
    val = validata.get("json").get("data")
    assert result == val


function_express = """
def {}(self, response, validata):
    with allure.step(response.pop('case_name')):
        validator(response, validata)"""


class CaseMetaClass(type):
    """
    根据接口调用的结果自动生成测试用例
    """
    def __new__(cls, name, bases, attrs):
        print(attrs)
        test_cases_data = attrs.pop('test_cases_data')
        for each in test_cases_data:
            api = each.pop('api')
            function_name = 'test' + api
            test_data = [tuple(x.values()) for x in each.get('responses')]
            function = gen_function(function_express.format(function_name),
                                    namespace={'validator': validator, 'allure': allure})
            # 集成allure
            story_function = allure.story('{}'.format(api.replace('_', '/')))(function)
            attrs[function_name] = pytest.mark.parametrize('response,validata', test_data)(story_function)

        return super().__new__(cls, name, bases, attrs)


def pytest_addoption(parser):
    parser.addoption("--tf",
                     action="store",
                     default=[],
                     type=list,
                     help="测试文件列表")
    parser.addoption(
        "--te",
        action="store",
        default="dev",
        type=str,
        help="当前测试的环境，默认为dev"
        )


@pytest.fixture(scope='session')
def generate_test_render(request):
    """
    测试用例生成处理
    :param request:
    :return:
    """
    var = request.config.getoption("--rootdir")
    test_file = request.config.getoption("--tf")
    env = request.config.getoption("--te")
    cases = []
    if test_file:
        case_file = "".join(test_file)
        if isinstance(case_file, str):
            cases = case_file.split(",")
    else:
        if os.path.isdir(var):
            for root, dirs, files in os.walk(var):
                if re.match(r'\w+', root):
                    if files:
                        cases.extend([os.path.join(root, file) for file in files if file.endswith('yaml')])

    data = main(cases, env)

    content = """
import allure

from conftest import CaseMetaClass


@allure.feature('{}接口测试({}项目)')
class Test{}API(object, metaclass=CaseMetaClass):

    test_cases_data = {}
"""
    test_cases_files = []
    if os.path.isdir(var):
        for root, dirs, files in os.walk(var):
            if not ('.' in root or '__' in root):
                if files:
                    case_name = os.path.basename(root)
                    project_name = os.path.basename(os.path.dirname(root))
                    test_case_file = os.path.join(root, 'test_{}.py'.format(case_name))
                    with open(test_case_file, 'w', encoding='utf-8') as fw:
                        fw.write(content.format(case_name, project_name,
                                                case_name.title(), data.get(root)))
                    test_cases_files.append(test_case_file)

    if test_file:
        temp = os.path.dirname(test_file)
        py_file = os.path.join(temp, 'test_{}.py'.format(os.path.basename(temp)))
    else:
        py_file = var

    pytest.main([
        '-v',
        py_file,
        '--alluredir',
        'report',
        '--te',
        env,
        '--capture',
        'no',
        '--disable-warnings',
    ])

    # for file in test_cases_files:
    #     os.remove(file)

    return test_cases_files
