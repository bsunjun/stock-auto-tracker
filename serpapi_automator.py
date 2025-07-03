{
  "nbformat": 4,
  "nbformat_minor": 0,
  "metadata": {
    "colab": {
      "provenance": [],
      "authorship_tag": "ABX9TyN5q6Gq1fmllsDKg8E4vQwj",
      "include_colab_link": true
    },
    "kernelspec": {
      "name": "python3",
      "display_name": "Python 3"
    },
    "language_info": {
      "name": "python"
    }
  },
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "view-in-github",
        "colab_type": "text"
      },
      "source": [
        "<a href=\"https://colab.research.google.com/github/bsunjun/stock-auto-tracker/blob/main/serpapi_automator.py\" target=\"_parent\"><img src=\"https://colab.research.google.com/assets/colab-badge.svg\" alt=\"Open In Colab\"/></a>"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": 5,
      "metadata": {
        "colab": {
          "base_uri": "https://localhost:8080/"
        },
        "id": "MHxOZSDVZW5e",
        "outputId": "099fae00-7029-417c-b933-a26d70668380"
      },
      "outputs": [
        {
          "output_type": "stream",
          "name": "stdout",
          "text": [
            "✅  저장 완료 (JSON / CSV)\n",
            "[main 9281a4d] 🗓️  update prices 2025-07-03 08:49:26\n",
            " 2 files changed, 67 insertions(+), 32 deletions(-)\n",
            " create mode 100644 current_prices.csv\n",
            " rewrite current_prices.json (71%)\n",
            "Enumerating objects: 6, done.\n",
            "Counting objects: 100% (6/6), done.\n",
            "Delta compression using up to 2 threads\n",
            "Compressing objects: 100% (4/4), done.\n",
            "Writing objects: 100% (4/4), 876 bytes | 876.00 KiB/s, done.\n",
            "Total 4 (delta 1), reused 0 (delta 0), pack-reused 0\n",
            "remote: Resolving deltas: 100% (1/1), completed with 1 local object.\u001b[K\n",
            "To https://github.com/bsunjun/stock-auto-tracker.git\n",
            "   a760bd6..9281a4d  HEAD -> main\n",
            "🚀  GitHub 푸시 완료\n",
            "📰 리노공업 주요 주주 美투자자문사, 지분 1% 장내매도\n",
            "📰 한 달 새 30% 뛰었다…리노공업, 실적 전망 톺아보니 [종목+]\n",
            "📰 리노공업, 5년째 이익률 40%…\"AP 전쟁 수혜\"\n"
          ]
        }
      ],
      "source": [
        "# [셀 1] — 키 주입\n",
        "from google.colab import userdata, output\n",
        "import os\n",
        "os.environ[\"SERPAPI_KEY\"] = userdata.get(\"SERPAPI_KEY\")   # 이미 쓰던 방식\n",
        "os.environ[\"GH_TOKEN\"]    = userdata.get(\"GH_TOKEN\")      # 새로 저장한 토큰\n",
        "\n",
        "# [셀 2] — 스クリ프트 실행\n",
        "!python serpapi_automator.py\n"
      ]
    }
  ]
}