import allure

from conftest import CaseMetaClass


@allure.feature('model_classification接口测试(auto_test_frame项目)')
class TestModel_ClassificationAPI(object, metaclass=CaseMetaClass):

    test_cases_data = [{'api': '_models_render_model', 'responses': [{'response': {'response': {'status': 1, 'msg': '请求成功', 'data': {'硬装': ['墙面', '背景墙', '地面', '吊顶', '构件'], '门窗': ['门', '窗', '窗帘'], '家具': ['家具组合', '沙发', '桌几', '床', '椅凳', '成品柜'], '装饰': ['灯饰', '柜架周边', '摆件', '人物/动物', '花卉/绿植'], '电器': ['厨房电器', '卫生间电器', '客厅电器', '书房电器', '阳台电器'], '厨卫': ['厨房用品', '卫浴用品'], '工装': ['餐饮空间', '办公空间', '展览馆', '学校教育', '商场超市', '店装']}}, 'url': 'https://test.eggrj.com/render_v2/models/render_model', 'arguments': {'model_content': 'classification'}, 'case_name': '模型分类列表'}, 'validator': {'json': {'data': {'硬装': ['墙面', '背景墙', '地面', '吊顶', '构件'], '门窗': ['门', '窗', '窗帘'], '家具': ['家具组合', '沙发', '桌几', '床', '椅凳', '成品柜'], '装饰': ['灯饰', '柜架周边', '摆件', '人物/动物', '花卉/绿植'], '电器': ['厨房电器', '卫生间电器', '客厅电器', '书房电器', '阳台电器'], '厨卫': ['厨房用品', '卫浴用品'], '工装': ['餐饮空间', '办公空间', '展览馆', '学校教育', '商场超市', '店装']}}}}]}]
