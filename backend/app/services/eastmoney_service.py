"""
东方财富网数据服务

提供实时股票行情数据、涨跌幅榜等数据
数据来源：东方财富网公开API
"""

import httpx
import re
import akshare as ak
from typing import Optional, Dict, Any, List
from app.core.logging import logger


class EastMoneyService:
    """东方财富网数据服务

    提供实时行情、涨跌幅榜等数据接口
    """

    def __init__(self):
        self.base_url = "https://push2.eastmoney.com/api/qt"
        self.timeout = 10

    async def get_stock_list(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_field: str = "f3",  # f3=涨跌幅
        sort_order: int = -1,  # -1=降序(涨幅榜), 1=升序(跌幅榜)
        filters: Optional[str] = None,  # 市场筛选条件
    ) -> Dict[str, Any]:
        """获取股票列表（实时行情）

        Args:
            page: 页码（从1开始）
            page_size: 每页数量
            sort_field: 排序字段
                f3: 涨跌幅
                f4: 涨跌额
                f5: 成交量
                f6: 成交额
                f2: 最新价
            sort_order: 排序方向
                -1: 降序（从大到小）
                1: 升序（从小到大）
            filters: 筛选条件（东方财富格式）
                m:0+t:6,m:0+t:80 - 深圳A股（主板+创业板）
                m:1+t:2,m:1+t:23 - 上海A股（主板+科创板）
                m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23 - 全部A股

        Returns:
            {
                "total": 总数量,
                "data": [
                    {
                        "code": "股票代码",
                        "name": "股票名称",
                        "price": 最新价,
                        "change_percent": 涨跌幅(%),
                        "change_amount": 涨跌额,
                        "volume": 成交量(手),
                        "amount": 成交额(元),
                        "high": 最高价,
                        "low": 最低价,
                        "open": 开盘价,
                        "last_close": 昨收价,
                    }
                ]
            }
        """
        try:
            # 默认筛选条件：全部A股
            if filters is None:
                filters = "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23"

            # 构建请求参数（使用标准格式，避免错误码102）
            import time
            params = {
                "pn": page,
                "pz": page_size,
                "po": 1 if sort_order == -1 else -1,  # 注意：东方财富的po参数与常规相反
                "np": 1,
                "fltt": 2,
                "invt": 2,
                "fid": sort_field,
                "fs": filters,
                "fields": (
                    "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,"
                    "f20,f21,f23,f24,f25,f22,f33,f11,f62,f128,f136,f115,f152"
                ),
                "_": int(time.time() * 1000),  # 时间戳（毫秒）
            }

            # 添加必要的headers
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Referer": "https://quote.eastmoney.com/center/",
                "Accept": "application/json",
            }

            # 发送请求
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/clist/get",
                    params=params,
                    headers=headers,
                )
                response.raise_for_status()
                result = response.json()

            # 解析数据
            if result.get("rc") != 0:
                logger.error(f"东方财富API返回错误: {result}")
                return {"total": 0, "data": []}

            data = result.get("data", {})
            total = data.get("total", 0)
            diff_list = data.get("diff", [])

            # 字段映射
            stocks = []
            for item in diff_list:
                stock = {
                    "code": item.get("f12"),  # 股票代码
                    "name": item.get("f14"),  # 股票名称
                    "price": item.get("f2"),  # 最新价
                    "change_percent": item.get("f3"),  # 涨跌幅(%)
                    "change_amount": item.get("f4"),  # 涨跌额
                    "volume": item.get("f5"),  # 成交量(手)
                    "amount": item.get("f6"),  # 成交额(元)
                    "high": item.get("f15"),  # 最高价
                    "low": item.get("f17"),  # 最低价
                    "open": item.get("f16"),  # 开盘价
                    "last_close": item.get("f18"),  # 昨收价
                    "turnover": item.get("f8"),  # 换手率
                }
                stocks.append(stock)

            logger.info(f"从东方财富获取股票列表: {len(stocks)}/{total}")
            return {"total": total, "data": stocks}

        except httpx.HTTPError as e:
            logger.error(f"请求东方财富API失败: {e}")
            return {"total": 0, "data": []}
        except Exception as e:
            logger.error(f"解析东方财富数据失败: {e}")
            return {"total": 0, "data": []}

    async def get_top_gainers(
        self,
        limit: int = 50,
        market: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取涨幅榜（涨幅最高的股票）

        Args:
            limit: 返回数量
            market: 市场筛选
                None: 全部A股
                "SZ": 深圳市场
                "SH": 上海市场
                "BJ": 北京市场

        Returns:
            {"total": 总数, "data": [股票列表]}
        """
        # 根据市场设置筛选条件
        filters_map = {
            "SZ": "m:0+t:6,m:0+t:80",  # 深圳主板+创业板
            "SH": "m:1+t:2,m:1+t:23",  # 上海主板+科创板
            "BJ": "m:0+t:81",  # 北京交易所
        }
        filters = filters_map.get(market)

        # 按涨跌幅降序排列（涨幅榜）
        return await self.get_stock_list(
            page=1,
            page_size=limit,
            sort_field="f3",  # 涨跌幅
            sort_order=-1,  # 降序
            filters=filters,
        )

    async def get_top_losers(
        self,
        limit: int = 50,
        market: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取跌幅榜（跌幅最大的股票）

        Args:
            limit: 返回数量
            market: 市场筛选

        Returns:
            {"total": 总数, "data": [股票列表]}
        """
        # 根据市场设置筛选条件
        filters_map = {
            "SZ": "m:0+t:6,m:0+t:80",
            "SH": "m:1+t:2,m:1+t:23",
            "BJ": "m:0+t:81",
        }
        filters = filters_map.get(market)

        # 按涨跌幅升序排列（跌幅榜）
        return await self.get_stock_list(
            page=1,
            page_size=limit,
            sort_field="f3",  # 涨跌幅
            sort_order=1,  # 升序（跌幅最大的在前）
            filters=filters,
        )

    async def get_top_volume(
        self,
        limit: int = 50,
        market: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取成交额榜（成交额最大的股票）

        Args:
            limit: 返回数量
            market: 市场筛选

        Returns:
            {"total": 总数, "data": [股票列表]}
        """
        filters_map = {
            "SZ": "m:0+t:6,m:0+t:80",
            "SH": "m:1+t:2,m:1+t:23",
            "BJ": "m:0+t:81",
        }
        filters = filters_map.get(market)

        # 按成交额降序排列
        return await self.get_stock_list(
            page=1,
            page_size=limit,
            sort_field="f6",  # 成交额
            sort_order=-1,  # 降序
            filters=filters,
        )

    async def get_market_overview(
        self,
        page_size: int = 5000,  # 获取足够多的股票来计算统计
    ) -> Dict[str, Any]:
        """获取市场概览数据（涨跌统计）

        从东方财富API获取实时市场数据，包括指数和涨跌统计

        Returns:
            {
                "indices": [指数列表],
                "stats": {
                    "limitUp": 57,  # 涨停家数
                    "limitDown": 6,  # 跌停家数
                    "zhabanRate": 25.97,  # 炸板率
                    "suggestPosition": 93,  # 建议仓位
                    "upCount": 2345,
                    "upPercent": 52.3,
                    "flatCount": 123,
                    "flatPercent": 2.7,
                    "downCount": 2012,
                    "downPercent": 45.0
                }
            }
        """
        try:
            import time

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 并发获取指数数据、涨跌停统计、涨跌分布
                import asyncio

                indices_task = self.get_sina_indices()
                ztb_stats_task = self._get_ztb_stats(client)  # 涨跌停对比、建议仓位等
                zdfb_stats_task = self._get_zdfb_stats(client)  # 涨跌分布数据

                results = await asyncio.gather(
                    indices_task,
                    ztb_stats_task,
                    zdfb_stats_task,
                    return_exceptions=True
                )

                indices = results[0] if not isinstance(results[0], Exception) else []
                ztb_stats = results[1] if not isinstance(results[1], Exception) else {}
                zdfb_stats = results[2] if not isinstance(results[2], Exception) else {}

                return {
                    "indices": indices,
                    "stats": {**ztb_stats, **zdfb_stats},  # 合并统计数据
                }

        except Exception as e:
            logger.error(f"获取市场概览失败: {e}")
            # 返回空数据
            return {
                "indices": [],
                "stats": {
                    "upCount": 0,
                    "upPercent": 0,
                    "flatCount": 0,
                    "flatPercent": 0,
                    "downCount": 0,
                    "downPercent": 0,
                    "limitUp": 0,
                    "limitDown": 0,
                },
            }

    async def _get_ztb_stats(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """从东方财富API获取涨停板统计数据

        使用官方API获取涨跌停对比、炸板率、建议仓位等数据

        Returns:
            {
                "limitUp": 57,  # 涨停家数
                "limitDown": 6,  # 跌停家数
                "zhabanRate": 25.97,  # 炸板率
                "suggestPosition": 93  # 建议仓位
            }
        """
        try:
            import time
            import json
            import asyncio

            headers = {
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://quote.eastmoney.com/ztb/",
            }

            # 并发请求三个API
            zdt_task = self._get_zdt_count(client, headers)
            dc_task = self._get_datacenter_stats(client, headers)

            results = await asyncio.gather(
                zdt_task,
                dc_task,
                return_exceptions=True
            )

            zdt_stats = results[0] if not isinstance(results[0], Exception) else {}
            dc_stats = results[1] if not isinstance(results[1], Exception) else {}

            # 合并统计数据
            stats = {**zdt_stats, **dc_stats}
            logger.info(f"从API获取统计数据: {stats}")
            return stats

        except Exception as e:
            logger.error(f"获取涨停板统计失败: {e}")
            return {}

    async def _get_zdt_count(self, client: httpx.AsyncClient, headers: dict) -> Dict[str, Any]:
        """获取涨跌停对比数据

        Returns:
            {"limitUp": 57, "limitDown": 6}
        """
        try:
            import time

            url = "https://push2ex.eastmoney.com/getTopicZDTCount"
            params = {
                "ut": "7eea3edcaed734bea9cbfc24409ed989",
                "dpt": "wz.ztzt",
                "time": "0",
                "_": str(int(time.time() * 1000))
            }

            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()

            # 返回的是JSON格式
            result = response.json()

            if result.get("rc") == 0:
                zdt_list = result.get("data", {}).get("zdtcount", [])
                if zdt_list:
                    # 取最新的一条数据（最后一个）
                    latest = zdt_list[-1]
                    limit_up = latest.get("ztc", 0)  # 涨停数
                    limit_down = latest.get("dtc", 0)  # 跌停数
                    return {"limitUp": limit_up, "limitDown": limit_down}

            return {}

        except Exception as e:
            logger.error(f"获取涨跌停对比失败: {e}")
            return {}

    async def _get_datacenter_stats(self, client: httpx.AsyncClient, headers: dict) -> Dict[str, Any]:
        """获取数据中心统计数据（建议仓位、炸板率等）

        Returns:
            {
                "suggestPosition": 93,
                "zhabanRate": 25.97,
                "sealingRate": 70.79
            }
        """
        try:
            import time

            url = "https://datacenter-web.eastmoney.com/web/api/data/v1/get"
            params = {
                "reportName": "RPT_CUSTOM_INTSELECTION_LIMIT",
                "columns": "LIMIT_NUMBERS,NATURAL_LIMIT,DAILY_LIMIT,TOUCH_LIMIT,SEALING_RATE,MONEYMAKING_EFFECT,POSITION_SUGGESTION",
                "source": "WEB",
                "client": "WEB",
                "_": str(int(time.time() * 1000))
            }

            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()

            result = response.json()

            if result.get("result"):
                data_list = result["result"].get("data", [])
                if data_list:
                    data = data_list[0]
                    return {
                        "suggestPosition": data.get("POSITION_SUGGESTION"),
                        "zhabanRate": round(100 - data.get("SEALING_RATE", 0), 2),  # 炸板率 = 100 - 封板率
                        "sealingRate": data.get("SEALING_RATE"),
                        "moneyMakingEffect": data.get("MONEYMAKING_EFFECT"),
                    }

            return {}

        except Exception as e:
            logger.error(f"获取数据中心统计失败: {e}")
            return {}

    async def _get_zdfb_stats(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """获取涨跌分布数据

        Returns:
            {
                "upCount": 2345,
                "upPercent": 52.3,
                "flatCount": 123,
                "flatPercent": 2.7,
                "downCount": 2012,
                "downPercent": 45.0
            }
        """
        try:
            import time
            import json

            url = "https://push2ex.eastmoney.com/getTopicZDFenBu"
            params = {
                "cb": "callbackdata7450391",
                "ut": "7eea3edcaed734bea9cbfc24409ed989",
                "dpt": "wz.ztzt",
                "_": str(int(time.time() * 1000))
            }

            headers = {
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://quote.eastmoney.com/ztb/",
            }

            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()

            # 返回的是JSONP格式：callbackname({...})
            text = response.text

            # 提取JSON部分
            import re
            json_match = re.search(r'\{.*\}', text)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)

                if result.get("rc") == 0:
                    fenbu_list = result.get("data", {}).get("fenbu", [])

                    # 解析涨跌分布
                    # 格式：{"-1": 1363, "0": 193, "1": 1191, ...}
                    # 负数表示跌幅，正数表示涨幅
                    up_count = 0
                    flat_count = 0
                    down_count = 0

                    for item in fenbu_list:
                        for key, value in item.items():
                            try:
                                change_range = int(key)
                                count = int(value)

                                if change_range < 0:
                                    down_count += count
                                elif change_range == 0:
                                    flat_count += count
                                else:
                                    up_count += count
                            except (ValueError, TypeError):
                                continue

                    total = up_count + flat_count + down_count
                    up_percent = round(up_count * 100 / total, 2) if total > 0 else 0
                    flat_percent = round(flat_count * 100 / total, 2) if total > 0 else 0
                    down_percent = round(down_count * 100 / total, 2) if total > 0 else 0

                    return {
                        "upCount": up_count,
                        "upPercent": up_percent,
                        "flatCount": flat_count,
                        "flatPercent": flat_percent,
                        "downCount": down_count,
                        "downPercent": down_percent,
                    }

            return {}

        except Exception as e:
            logger.error(f"获取涨跌分布失败: {e}")
            return {}

    async def _get_market_stats(
        self,
        client: httpx.AsyncClient,
        headers: dict,
    ) -> Dict[str, Any]:
        """获取市场统计数据（涨跌分布、涨跌停统计）

        通过东方财富API获取全部A股的实时行情数据，计算统计信息

        Returns:
            {
                "upCount": 2345,
                "upPercent": 52.3,
                "flatCount": 123,
                "flatPercent": 2.7,
                "downCount": 2012,
                "downPercent": 45.0,
                "limitUp": 45,
                "limitDown": 12
            }
        """
        try:
            import time
            import asyncio
            import akshare as ak

            # 使用AKShare获取全部A股实时行情数据
            # AKShare的 stock_zh_a_spot_em() 返回所有A股的实时数据
            all_stocks = []
            try:
                df = ak.stock_zh_a_spot_em()

                # 转换为统计所需的格式
                # AKShare返回的列包括: 代码, 名称, 最新价, 涨跌幅, 涨跌额, 成交量, 成交额等
                for _, row in df.iterrows():
                    change_pct = row.get('涨跌幅', 0)
                    if isinstance(change_pct, str):
                        try:
                            change_pct = float(change_pct.replace('%', ''))
                        except:
                            change_pct = 0

                    all_stocks.append({
                        "f3": change_pct,  # 涨跌幅
                        "f14": row.get('名称', ''),  # 股票名称（用于排除ST）
                    })

                logger.info(f"从AKShare获取市场数据: {len(all_stocks)} 只股票")

            except Exception as e:
                logger.error(f"AKShare获取实时行情失败: {e}，回退到东方财富API")
                # 回退到东方财富API（仅获取部分数据）
                params = {
                    "pn": 1,
                    "pz": 1000,
                    "po": 1,
                    "np": 1,
                    "fltt": 2,
                    "invt": 2,
                    "fid": "f3",
                    "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
                    "fields": "f3,f4,f12,f14",
                    "_": int(time.time() * 1000),
                }

                response = await client.get(
                    f"{self.base_url}/clist/get",
                    params=params,
                    headers=headers,
                )
                response.raise_for_status()
                result = response.json()

                if result.get("rc") == 0:
                    diff_list = result.get("data", {}).get("diff", [])
                    all_stocks = diff_list
                    logger.warning(f"使用东方财富API回退数据: {len(all_stocks)} 只股票")

            # 计算涨跌统计
            up_count = 0
            flat_count = 0
            down_count = 0
            limit_up = 0
            limit_down = 0
            total_valid_stocks = 0

            for stock in all_stocks:
                # 排除ST股票
                stock_name = stock.get("f14", "")
                if "ST" in stock_name or "退" in stock_name:
                    continue

                total_valid_stocks += 1
                change_pct = stock.get("f3", 0)  # 涨跌幅

                if change_pct > 0:
                    up_count += 1
                    # 主板10%涨停，创业板/科创板20%涨停
                    if change_pct >= 9.9:  # 涨停（约10%）
                        limit_up += 1
                elif change_pct < 0:
                    down_count += 1
                    if change_pct <= -9.9:  # 跌停（约-10%）
                        limit_down += 1
                else:
                    flat_count += 1

            # 计算百分比
            up_percent = round(up_count * 100 / total_valid_stocks, 2) if total_valid_stocks > 0 else 0
            flat_percent = round(flat_count * 100 / total_valid_stocks, 2) if total_valid_stocks > 0 else 0
            down_percent = round(down_count * 100 / total_valid_stocks, 2) if total_valid_stocks > 0 else 0

            logger.info(
                f"市场统计: 总数{total_valid_stocks} (上涨{up_count}, 平盘{flat_count}, "
                f"下跌{down_count}, 涨停{limit_up}, 跌停{limit_down})"
            )

            stats = {
                "upCount": up_count,
                "upPercent": up_percent,
                "flatCount": flat_count,
                "flatPercent": flat_percent,
                "downCount": down_count,
                "downPercent": down_percent,
                "limitUp": limit_up,
                "limitDown": limit_down,
            }

            return stats

        except Exception as e:
            logger.error(f"获取市场统计数据失败: {e}")
            # 返回空数据
            return {
                "upCount": 0,
                "upPercent": 0,
                "flatCount": 0,
                "flatPercent": 0,
                "downCount": 0,
                "downPercent": 0,
                "limitUp": 0,
                "limitDown": 0,
            }

    async def get_sina_indices(self) -> List[Dict[str, Any]]:
        """使用新浪财经API获取主要指数实时数据

        新浪财经提供实时的指数行情数据
        数据格式：sh000001 = 上证指数, sz399001 = 深证成指

        Returns:
            [
                {
                    "name": "上证指数",
                    "code": "sh000001",
                    "value": 3964.22,
                    "change": -0.89,
                    "changePercent": -0.02
                },
                ...
            ]
        """
        try:
            # 定义要获取的指数列表
            index_list = [
                ("sh000001", "上证指数"),
                ("sz399001", "深证成指"),
                ("sh000300", "沪深300"),
                ("sz399006", "创业板指"),
                ("sh000688", "科创50"),
            ]

            # 构建新浪指数API URL
            # 格式：s_sh000001=上证指数,3965.12,3.72,3961.40,3973.23,3961.40,3965.12,1176257360000,0,0,0,0
            codes = ",".join([code.replace("sh", "s_").replace("sz", "s_") for code, _ in index_list])
            url = f"http://hq.sinajs.cn/list={codes}"

            headers = {
                "User-Agent": "Mozilla/5.0",
                "Referer": "http://finance.sina.com.cn/",
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                text = response.text

            indices = []
            lines = text.strip().split('\n')

            for i, line in enumerate(lines):
                if not line or i >= len(index_list):
                    continue

                # 解析数据
                # 格式：var hq_str_sh000001="上证指数,3965.12,3.72,3961.40,..."
                try:
                    if 'hq_str_' in line:
                        start = line.find('"') + 1
                        end = line.rfind('"')
                        data_str = line[start:end]

                        if not data_str:
                            continue

                        parts = data_str.split(',')
                        if len(parts) < 4:
                            continue

                        name = parts[0]
                        price = float(parts[1])  # 最新价
                        change = float(parts[2])  # 涨跌额
                        last_close = float(parts[3])  # 昨收

                        # 计算涨跌幅
                        change_pct = round((change / last_close) * 100, 2) if last_close != 0 else 0

                        # 获取代码
                        code = index_list[i][0]

                        indices.append({
                            "name": name,
                            "code": code,
                            "value": price,
                            "change": change,
                            "changePercent": change_pct,
                        })

                except (ValueError, IndexError) as e:
                    logger.warning(f"解析指数数据失败: {line[:50]}... - {e}")
                    continue

            logger.info(f"从新浪财经获取实时指数数据: {len(indices)} 个指数")

            # 如果新浪财经返回空数据，使用东方财富备用API
            if len(indices) == 0:
                logger.warning("新浪财经API返回空数据，使用东方财富备用API")
                return await self._get_indices_from_eastmoney()

            return indices

        except Exception as e:
            logger.error(f"获取指数数据失败: {e}")
            # 如果新浪财经失败，尝试使用东方财富备用API
            try:
                logger.info("尝试使用东方财富备用API获取指数数据")
                return await self._get_indices_from_eastmoney()
            except Exception as e2:
                logger.error(f"东方财富备用API也失败: {e2}")
                return []

    async def _get_indices_from_eastmoney(self) -> List[Dict[str, Any]]:
        """从东方财富API获取指数数据（备用方案）

        使用 ulist.np/get API 获取指数数据

        Returns:
            指数列表
        """
        try:
            import time

            # 指数代码映射（东方财富格式）
            index_codes = [
                ("1.000001", "上证指数"),
                ("0.399001", "深证成指"),
                ("1.000300", "沪深300"),
                ("0.399006", "创业板指"),
                ("1.000688", "科创50"),
            ]

            # 构建secids参数
            secids = ",".join([code for code, _ in index_codes])

            headers = {
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://quote.eastmoney.com/",
            }

            params = {
                "fields": "f1,f2,f3,f4,f12,f13,f14",  # f2=最新价, f3=涨跌幅, f4=涨跌额
                "secids": secids,
                "_": int(time.time() * 1000),
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://push2.eastmoney.com/api/qt/ulist.np/get",
                    params=params,
                    headers=headers,
                )
                response.raise_for_status()
                result = response.json()

            indices = []
            if result.get("rc") == 0:
                diff_list = result.get("data", {}).get("diff", [])

                for item in diff_list:
                    try:
                        name = item.get("f14", "")
                        code = item.get("f12", "")
                        market = item.get("f13", 0)

                        # 构建完整代码
                        full_code = f"{'sh' if market == 1 else 'sz'}{code}"

                        price = item.get("f2", 0) / 100  # 最新价
                        change_pct = item.get("f3", 0) / 100  # 涨跌幅(%)
                        change = item.get("f4", 0) / 100  # 涨跌额

                        indices.append({
                            "name": name,
                            "code": full_code,
                            "value": round(price, 2),
                            "change": round(change, 2),
                            "changePercent": round(change_pct, 2),
                        })

                    except Exception as e:
                        logger.warning(f"解析指数数据失败: {item} - {e}")
                        continue

            logger.info(f"从东方财富获取指数数据: {len(indices)} 个指数")
            return indices

        except Exception as e:
            logger.error(f"从东方财富获取指数失败: {e}")
            return []


# 创建全局实例
eastmoney_service = EastMoneyService()
