# 大糖帝国（Sugarscape）

这是一个使用 Python、NumPy 和 Matplotlib 编写的 Sugarscape 代理模型。每位居民拥有不同的视野、代谢、寿命、性别和财富，并遵循以下规则：

- 糖山上的资源会逐步再生；
- 居民在视野内选择糖最多且距离最近的空格移动；
- 居民收获糖、消耗代谢，财富耗尽或寿终时死亡；
- 相邻的适龄居民可在空格中繁殖，并共同支付繁殖成本；
- 程序实时统计人口、平均财富和基尼系数。

## 运行

在当前目录打开 PowerShell：

```powershell
python sugarscape.py
```

常用示例：

```powershell
# 使用固定随机种子运行动画
python sugarscape.py --seed 42 --agents 300 --steps 500

# 后台完成模拟并导出统计数据
python sugarscape.py --no-gui --seed 42 --steps 1000 --csv output/stats.csv

# 关闭繁殖，观察固定初始人口的衰亡过程
python sugarscape.py --no-reproduction --steps 300

# 保存动画（GIF 需要 Pillow，MP4 需要 FFmpeg）
python sugarscape.py --steps 200 --save empire.gif
```

查看所有参数：

```powershell
python sugarscape.py --help
```

## 测试

```powershell
python -m unittest -v
```

项目正常运行只需要现有的 NumPy 和 Matplotlib；仅保存动画时可能需要额外的 Pillow 或 FFmpeg。
