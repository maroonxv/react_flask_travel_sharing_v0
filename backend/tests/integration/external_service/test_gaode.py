import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))
from app_travel.infrastructure.external_service.gaode_geo_service_impl import GaodeGeoServiceImpl
from app_travel.domain.value_objects.travel_value_objects import Location

class TestGaodeGeoServiceIntegration:
    """高德地图服务集成测试（调用真实 API）"""
    
    @pytest.fixture
    def geo_service(self):
        # 使用用户提供的真实 Key
        return GaodeGeoServiceImpl(api_key="615fc65de7dcae0a3b68b67ca8746591")

    def test_geocode_real(self, geo_service):
        """测试地理编码：地址 -> 坐标"""
        # 测试一个知名地标，确保返回稳定
        address = "北京市天安门"
        location = geo_service.geocode(address)
        
        assert location is not None
        assert location.name == address
        assert location.has_coordinates()
        # 天安门大概坐标 (116.397, 39.908)
        assert 116.3 < location.longitude < 116.5
        assert 39.8 < location.latitude < 40.0
        assert "北京" in location.address

    def test_geocode_invalid(self, geo_service):
        """测试无效地址"""
        # 一个极大概率无法解析的地址
        location = geo_service.geocode("!@#$%^&*()_INVALID_ADDRESS_12345")
        assert location is None

    def test_reverse_geocode_real(self, geo_service):
        """测试逆地理编码：坐标 -> 地址"""
        # 天安门坐标
        lat, lng = 39.908722, 116.397496
        address = geo_service.reverse_geocode(lat, lng)
        
        assert address is not None
        assert "北京" in address
        assert "东城" in address or "西城" in address

    def test_calculate_distance_real(self, geo_service):
        """测试距离计算"""
        # 北京 -> 上海 (直线距离约 1000km+)
        origin = Location(name="Beijing", latitude=39.9042, longitude=116.4074)
        dest = Location(name="Shanghai", latitude=31.2304, longitude=121.4737)
        
        distance = geo_service.calculate_distance(origin, dest)
        
        # 验证距离在合理范围内 (1000km - 1300km)
        assert distance > 1000000 # > 1000km
        assert distance < 1300000 # < 1300km

    def test_calculate_distance_with_geocoding(self, geo_service):
        """测试自动触发地理编码的距离计算"""
        # 只提供地名，不提供坐标
        origin = Location(name="北京西站")
        dest = Location(name="北京南站")
        
        distance = geo_service.calculate_distance(origin, dest)
        
        # 两站之间距离大概 10km 左右
        assert distance > 0
        assert distance < 20000 # < 20km

    def test_get_route_driving(self, geo_service):
        """测试驾车路线规划"""
        origin = Location(name="Start", latitude=39.9042, longitude=116.4074) # 北京
        dest = Location(name="End", latitude=39.1256, longitude=117.1987) # 天津
        
        route = geo_service.get_route(origin, dest, mode="driving")
        
        assert route is not None
        assert "paths" in route
        assert len(route["paths"]) > 0
        
        path = route["paths"][0]
        assert path["distance"] > 100000 # > 100km
        assert path["duration"] > 3600 # > 1 hour
        assert path["steps"] > 0

    def test_search_places_keyword(self, geo_service):
        """测试关键字搜索"""
        keyword = "清华大学"
        results = geo_service.search_places(keyword)
        
        assert len(results) > 0
        first_match = results[0]
        assert "清华" in first_match.name
        assert first_match.has_coordinates()

    def test_search_places_around(self, geo_service):
        """测试周边搜索"""
        # 以天安门为中心，搜附近的"咖啡"
        center = Location(name="Center", latitude=39.9087, longitude=116.3975)
        results = geo_service.search_places("咖啡", location=center, radius=1000)
        
        assert len(results) > 0
        # 验证结果确实有坐标
        for res in results:
            assert res.has_coordinates()
            assert res.latitude is not None
            assert res.longitude is not None
