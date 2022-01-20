export default function Content({children}) {
    return (
        <div className="flex-grow bg-slate-700 overflow-hidden p-4 pl-6 pt-8 text-white">
            {children}
        </div>
    )
}
