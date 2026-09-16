from dataclasses	import dataclass


@dataclass
class LikeResult:
	
	total	: int
	success	: int	= 0
	
	@property
	def fail(self) -> int:
		return self.total - self.success
	
	def add_success(self, n: int = 1) -> None:
		self.success += n