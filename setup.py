from distutils.core import setup
setup(name='ecap',
      version='1.0',
      author='eric',
      py_modules=[
          'core.Util','core.zoom',
          'monitor.CompView','monitor.MarketWidth','monitor.TrendRank',
          'pattern.Radar','pattern.TrendBreaking','pattern.TrendFin','pattern.TriNet',
          'quant.force','quant.kdj','quant.MACD','quant.nineTurn','quant.MoveMentROC','quant.Pivot','quant.Trix','quant.Util','quant.weekTrend'
      ]
      )