import { useState, useRef, useEffect } from 'react'
import { Search, Loader2 } from 'lucide-react'
import { useStockSearch } from '../../hooks/useStocks'
import { StockSearchResult } from '../../types'
import { cn } from '../../lib/utils'
import { Input } from '../ui/Input'

interface StockSearchProps {
  onSelect: (stock: StockSearchResult) => void
  className?: string
}

export function StockSearch({ onSelect, className }: StockSearchProps) {
  const [inputValue, setInputValue] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [isOpen, setIsOpen] = useState(false)

  // Only search when searchQuery is updated (by button or enter)
  // Or should we keep auto-search? User asked for "Search Button". Usually implies manual trigger or explicit action.
  // But hybrid is good. Let's keep auto-search behavior IF desired, or strictly manual?
  // User said "also create a search button".
  // Let's make it so typing DOES NOT search automatically if we want strictly manual, OR we keep auto but add button for clarity/forcing.
  // Given "When key-in it seems to work", auto is there.
  // Let's support both: Type -> Auto (optional/debounce) OR Type -> Click Button -> Search.
  // The user complaint "ESC not working" -> Fix ESC.
  // "Make manual button" -> Add button.
  // To avoid double fetching, let's decouble input and search query.

  const { data: results, isLoading, refetch } = useStockSearch(searchQuery)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Fix ESC key
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setIsOpen(false)
      // Optional: Clear query? Maybe just close.
    }
    if (e.key === 'Enter') {
      e.preventDefault()
      triggerSearch()
    }
  }

  const triggerSearch = () => {
    if (inputValue.trim()) {
      setSearchQuery(inputValue)
      setIsOpen(true)
      // Ensure refetch helps if query didn't change but we want to reopen/retry
      setTimeout(() => refetch(), 0)
    }
  }

  // Debounce effect for auto-search if desired? 
  // User said "works when keyed in", implying auto-search exists and is okay, but wanted button too.
  // But maybe they want to STOP auto search? 
  // "when key-in it works... but also add button"
  // Let's bind search to inputValue with debounce normally, but let's strictly follow request for button.
  // I will make it manual + enter for now to be safe and efficient, or hybrid.
  // Let's try Hybrid: Input updates immediate, but separate Effect updates SearchQuery after delay?
  // For now, let's stick to EXPLICIT trigger since a button was requested. It's cleaner.
  // Wait, if I type 'Samsung', I want results. 
  // I will implement: Typing updates input. Enter or Button updates `searchQuery`. 
  // `useStockSearch` watches `searchQuery`.

  const handleSelect = (stock: StockSearchResult) => {
    onSelect(stock)
    setInputValue('')
    setSearchQuery('')
    setIsOpen(false)
  }

  return (
    <div ref={containerRef} className={cn('relative', className)}>
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <Input
            placeholder="종목명 또는 코드 검색..."
            value={inputValue}
            onChange={(e) => {
              setInputValue(e.target.value)
              // If we want auto-search while typing, uncomment below:
              setSearchQuery(e.target.value)
              setIsOpen(true)
            }}
            onKeyDown={handleKeyDown}
            className="pl-9"
          />
        </div>
        <button
          type="button"
          onClick={triggerSearch}
          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors"
        >
          검색
        </button>
      </div>

      {isOpen && (searchQuery.length > 0) && (
        <div className="absolute z-10 mt-1 w-full overflow-hidden rounded-lg border border-gray-200 bg-white shadow-lg ring-1 ring-black ring-opacity-5">
          {isLoading ? (
            <div className="p-4 flex items-center justify-center gap-2 text-sm text-gray-500">
              <Loader2 className="h-4 w-4 animate-spin" /> 검색 중...
            </div>
          ) : results && results.length > 0 ? (
            <ul className="max-h-60 overflow-auto py-1">
              {results.map((stock) => (
                <li
                  key={`${stock.market_type}-${stock.ticker}`}
                  className="cursor-pointer px-4 py-2 hover:bg-gray-50 flex items-center justify-between"
                  onClick={() => handleSelect(stock)}
                >
                  <div>
                    <div className="font-medium text-gray-900">{stock.name}</div>
                    <div className="text-xs text-gray-500">{stock.ticker}</div>
                  </div>
                  <div className="text-right">
                    <span className={cn(
                      "text-xs px-1.5 py-0.5 rounded font-medium",
                      stock.market_type === 'KR' ? "bg-blue-50 text-blue-600" : "bg-violet-50 text-violet-600"
                    )}>
                      {stock.market_type}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="p-4 text-center text-sm text-gray-500">검색 결과가 없습니다</div>
          )}
        </div>
      )}
    </div>
  )
}
