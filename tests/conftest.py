import pytest

KO_CHAT = """User: React에서 useEffect 무한 루프가 발생하는 이유를 알려줘
Assistant: useEffect 무한 루프는 의존성 배열에 매 렌더마다 새로 생성되는 객체나 함수가 들어갈 때 발생합니다. 상태 업데이트가 effect 안에서 일어나고 그 상태가 의존성 배열에 있으면 렌더링이 반복됩니다. useCallback과 useMemo로 참조를 고정하세요.
User: useCallback 의존성 배열 예제 코드 보여줘
Assistant: 다음은 useCallback 예제입니다.
```js
const fetchData = useCallback(() => { api.get(id) }, [id]);
```
의존성 배열에 id만 넣으면 됩니다.
User: 아니 그게 아니라 TypeScript로 작성해줘
Assistant: 죄송합니다. TypeScript 버전입니다.
```ts
const fetchData = useCallback((): void => { api.get(id) }, [id]);
```
User: 고마워
Assistant: 천만에요! 더 궁금한 점이 있으면 언제든 물어보세요. useEffect와 useCallback을 잘 활용하시길 바랍니다.
User: 그런데 파이썬 pandas 데이터프레임 병합 방법도 알려줘
Assistant: pandas에서는 merge, join, concat을 사용합니다. pd.merge(df1, df2, on='key')처럼 키 기준으로 병합합니다.
User: 고마워요
Assistant: 별말씀을요! 즐거운 코딩 되세요.
"""

EN_CHAT = """User: How do I configure nginx as a reverse proxy for a node application?
Assistant: Create a server block with proxy_pass pointing at your node application port, set proxy headers such as Host and X-Forwarded-For, and reload nginx. A typical node application listens on port 3000.
User: How do I configure nginx as a reverse proxy for my node application?
Assistant: Use a location block with proxy_pass http://localhost:3000; and include proxy_set_header directives for the node application.
User: add websocket support to the nginx proxy config
Assistant: For websocket support add proxy_http_version 1.1 and the Upgrade and Connection headers to the nginx location block.
User: continue
Assistant: Then reload nginx with nginx -s reload and test the websocket connection.
User: thanks!
Assistant: You're welcome! Good luck with your nginx setup and your node application.
"""


@pytest.fixture
def ko_chat():
    return KO_CHAT


@pytest.fixture
def en_chat():
    return EN_CHAT
