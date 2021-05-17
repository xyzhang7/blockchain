# blockchain

## 功能
* 捐款方：
	* 捐赠目标
		* 有明确的捐赠对象 -> `Donate()`
		* 无明确的捐赠对象 -> 推荐/关键词选择/调度算法`schedular`
* 收款方：
	* 需求金额
	* 收款上限
		* 目标金额（进度条）
		* 单次收款上限？(50w, 20w, 10w, 5w)
		* 总收款上限？
		* 如何界定？（experience | 信用评级）
	* priority 排序 | 切片 
		* `max priority queue` 
			* 当上一笔捐款完成时调用`extract-max`获取priority最高的
			* `schedular`可以调用`insert`将新的需求加入queue
			* `priority`规则：
				* 时间增加，`priority`增加
				* 信用评级？ 
					* 激励机制：提供的信息更加全面、即时的
					* 举报机制
					* 人工选核
				* 紧急/重要程度？
		* 切片
			* 备用善款（并不将所有可用资金都立即分配）
			* 善款数额 < 需求：
				* 资金如何切片？
* 第三方：
	* 捐款结果查询 -> 监听`Donate()`事件
	
## 设计模式
* Security?
* Maintenance?
* Authorization?
