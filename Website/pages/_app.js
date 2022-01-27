import '../styles.css'
import {ThemeProvider} from "next-themes";
import {SessionProvider} from 'next-auth/react'
import {SWRConfig} from 'swr'

export default function App({Component, pageProps}) {
    return (
        <SessionProvider session={pageProps.session}>
            <SWRConfig value={{provider: () => new Map()}}>
                <ThemeProvider
                    forcedTheme={Component.theme || undefined}
                    attribute="class"
                    disableTransitionOnChange={true}
                    defaultTheme="dark"
                >
                    <Component {...pageProps} />
                </ThemeProvider>
            </SWRConfig>
        </SessionProvider>
    )
}
