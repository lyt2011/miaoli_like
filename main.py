from ncatbot.plugin		import NcatBotPlugin
from ncatbot.core		import registrar
from ncatbot.event.qq	import MessageEvent
from ncatbot.api.errors	import APIError

from .models	import LikeResult

import asyncio


PLUGIN_NAME	= "喵璃の点赞扩展"


# TODO: 后续引入点赞状态持久化
class MiaoLiLike(NcatBotPlugin):
	
	def __init__(self, *args, **kwargs) -> None:
		
		super().__init__(*args, **kwargs)
		
		self.total_max_likes: int = 50 # 一个用户的最大赞
	
	async def on_load(self) -> None:
		
		if "total_max_likes" in self.config:
			self.total_max_likes = self.config["total_max_likes"]
		
		self.logger.info(f"{PLUGIN_NAME} 已加载")
	
	async def on_close(self) -> None:
		self.logger.info(f"{PLUGIN_NAME} 已卸载")
	
	async def send_like(self, user_id: Union[str, int], *, n: int = 1) -> None:
		
		"""给 user_id 进行 n 次点赞"""
		
		self.logger.debug(f"尝试为 {user_id} 点赞 {n} 次")
		await self.api.qq.messaging.send_like(user_id=user_id, times=n)
		self.logger.debug(f"成功为 {user_id} 点赞 {n} 次")
	
	async def smart_like(self, user_id: Union[str, int]) -> LikeResult:
		
		"""
		更聪明的点赞
		返回 LikeResult (dataclass)，便于统计信息
		"""
		like_result	= LikeResult(total=self.total_max_likes)
		
		for _ in range(self.total_max_likes):
			
			try:
				await self.send_like(user_id=user_id)
				await asyncio.sleep(0.5)
			
			except APIError:
				pass # 暂时不写逻辑 因为用不上
			
			except Exception as e:
				self.logger.exception(f"smart_like 执行过程中出现: {e}")
			
			else:
				like_result.add_success(1)
		
		return like_result
	
	@registrar.on_command("赞我")
	async def on_like_command(self, event: MessageEvent) -> None:
	
		"""
		先计算 "以最大数量给用户点赞，需要多少次" 与 "还剩下多少次"
		然后根据结果 先 for 循环点赞固定次数 然后单独点赞剩下的次数
		"""
		
		self.logger.info(f"{event.user_id} 触发点赞")
		
		like_result = await self.smart_like(user_id=event.user_id)
		
		self.logger.info(
			f"共 {like_result.total} 次 | "
			f"成功 {like_result.success} 次 | "
			f"失败 {like_result.fail} 次"
		)
		
		await event.reply(f"给杂鱼赞了 {like_result.success} 次喵")
		
		return