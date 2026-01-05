 我的需求，需要生成一个新文件，把我定义的规则满足的报警
 生成 curl 请求。放到 message 中。
 
curl --location 'https://fwalert.com/96a-b4-4c8f-bdbc-9f298598ead7' \
--header 'Content-Type: application/json' \
--data '{
    "message": "BNB 价格在过去五分钟涨了 30%，请及时关注"
}'

放到这个 message中，类似于这样，我会提供 url 到 env 中。你需要帮我完成这个 py 文件，并且告诉我怎么用，写个文档。